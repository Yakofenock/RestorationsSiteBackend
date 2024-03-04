from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from Restorations.models import Restoration, Work, Payment, Donation
from django.db.models import Q, Sum

from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsAdmin, IsManager, IsUser
from .serialisers import RestorationSerialiser, PaymentSerializer, WorkSerialiser
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound, MethodNotAllowed
from Restorations.utils import RESTORATION_STATUSES, WORK_STATUSES, PAYMENT_STATUSES
from datetime import datetime

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from Site.settings import WEB_SERVICE_SEKRET_KEY


def add_count_option(instance, request: Request):
    if request.GET.get('count') == 'true':
        queryset = instance.get_queryset()
        return Response({'count': queryset.count()})


def get_model_obj(model, pk, force_empty=False):
    obj = model.objects.filter(id=pk).first()
    if not obj and not force_empty:
        raise NotFound({'detail': 'object not found'})
    return obj


def get_draft(request):
    return Payment.objects.filter(user=request.user.id,
                                  status=PAYMENT_STATUSES[0]).first()


class RestorationViewSet(ModelViewSet):
    serializer_class = RestorationSerialiser
    queryset = Restoration.objects.none()
    http_method_names = ['get', 'post', 'delete', 'put']

    def get_permissions(self):
        match self.action:
            case 'list' | 'retrieve':
                permission_classes = [IsAuthenticatedOrReadOnly]
            case _:
                permission_classes = [IsManager | IsAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        restorations = Restoration.objects.all()

        user = self.request.user # Дефолтный юзер имеет права администратора
        if not user.is_superuser and not user.is_staff:
            restorations = restorations.filter(status=RESTORATION_STATUSES[1])

        filter = self.request.GET.get('filter')
        match filter:
            case "Forming":
                restorations = restorations.filter(status=RESTORATION_STATUSES[0])
            case "InProcess":
                restorations = restorations.filter(status=RESTORATION_STATUSES[1])
            case "Completed":
                restorations = restorations.filter(status=RESTORATION_STATUSES[-1])
            case _:
                ...

        # Processing search:
        search = self.request.GET.get('search')
        if search:
            restorations = restorations.filter(
                Q(name__icontains=search) | Q(description__icontains=search) |
                Q(work__name__icontains=search)
            ).distinct()  # Last query can put few same result

        return restorations

    def list(self, request: Request, *args, **kwargs):
        result = add_count_option(self, request)
        if result:
            return result

        work_id = request.GET.get('work_id')
        if work_id:
            work = Work.objects.filter(pk=work_id).first()
            if not work:
                raise NotFound({'detail': 'there is not such work'})
            return Response(self.serializer_class(work.restore, many=False,
                                                  context={'specific': request}).data)

        draft = get_draft(request)
        data = self.serializer_class(self.get_queryset(), many=True,
                                     context={'request': request}).data
        return Response({
            'draft_id': draft.id if draft else None,
            'restorations_list': data
        })

    def destroy(self, request: Request,  *args, **kwargs):
        restoration = get_model_obj(Restoration, kwargs.get('pk'))
        if restoration.status == RESTORATION_STATUSES[-1]:
            raise NotFound({'detail': 'this restoration already deleted'})

        restoration.status = RESTORATION_STATUSES[-1]
        restoration.save()
        return Response(status=204)


class WorkViewSet(ModelViewSet):
    serializer_class = WorkSerialiser
    queryset = Work.objects.all()

    # По каким-то причинам без описания реализаций методов блокирует к ним доступ:
    # http_method_names = ['get', 'post', 'put' 'delete']

    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='GET')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='DELETE')


def validate_date(date: str, field: str):
    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValidationError({'detail': field + ' field date format is incorrect.'})


# Getting and logically deleting payments:
class PaymentViewSet(ModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.none()

    http_method_names = ['get', 'delete']

    def get_permissions(self):
        permission_classes = []
        match self.action:
            # Viewing of all list is protected from user:
            case 'list' | 'retrieve':
                permission_classes = [IsUser | IsManager | IsAdmin]
            case 'destroy':
                permission_classes = [IsUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        payments = Payment.objects.all().exclude(status__in=[PAYMENT_STATUSES[0],
                                                             PAYMENT_STATUSES[-1]])

        # Viewing of all list protection from user:
        user = self.request.user
        if not user.is_superuser and not user.is_staff:
            payments = payments.filter(user=user.id)

        # Filters:
        code = self.request.GET.get('code')
        if code:
            payments = payments.filter(code=code)

        start = self.request.GET.get('start_date')
        if start:
            payments = payments.filter(date_open__gte=validate_date(start, 'start_date'))

        end = self.request.GET.get('end_date')
        if end:
            payments = payments.filter(date_open__lte=validate_date(end, 'end_date'))

        status = self.request.GET.get('status')
        if status:
            if status not in PAYMENT_STATUSES:
                raise ValidationError({'detail': 'wrong status specified'})
            payments = payments.filter(status=status)

        return payments

    def list(self, request: Request, *args, **kwargs):
        result = add_count_option(self, request)
        if result:
            return result

        # Ability to check summ of all payments matching query:
        if request.GET.get('sum') == 'true':
            return Response({
                'today_requested':
                    self.get_queryset().aggregate(summ_req=Sum('work__donation__sum'))['summ_req']
            })

        return super().list(request, args, kwargs)

    def retrieve(self, request, *args, **kwargs):
        payment = get_model_obj(Payment, kwargs.get('pk'))  # Because get_queryset takes opened away
        if payment.status == PAYMENT_STATUSES[-1]:
            raise NotFound({'detail': 'payment not found'})

        if payment.user != request.user and not (request.user.is_staff or request.user.is_admin):
            raise PermissionDenied()

        return Response(self.get_serializer(payment).data)

    def destroy(self, request: Request, *args, **kwargs):
        payment = get_model_obj(Payment, kwargs.get('pk'))  # Same

        # Not to allow to user to delete other users payments:
        if payment.user != request.user:
            raise PermissionDenied()

        if payment.status == PAYMENT_STATUSES[-1]:
            raise NotFound({'detail': 'this payment already deleted'})

        payment.status = PAYMENT_STATUSES[-1]
        payment.save()
        return Response(status=204)


# Manging status of payment for admin:
class PaymentStatusAdminView(APIView):
    permission_classes = [IsManager | IsAdmin]

    def put(self, request, *args, **kwargs):
        payment = get_model_obj(Payment, kwargs.get('pk'))

        if payment.status == PAYMENT_STATUSES[-1]:
            raise NotFound({'detail': 'there is no such payment'})

        if payment.status not in [PAYMENT_STATUSES[1], PAYMENT_STATUSES[2]]:
            raise PermissionDenied({'detail': 'you cant change status now'})

        status = request.data.get('status')
        if status not in [PAYMENT_STATUSES[-3], PAYMENT_STATUSES[-2]]:
            raise PermissionDenied({'detail': 'wrong status specified'})

        payment.manager = request.user
        payment.status = status
        payment.save()

        return Response(PaymentSerializer(payment).data)


# Manging status of payment for user:
class PaymentStatusUserView(APIView):
    permission_classes = [IsUser]
    def put(self, request, *args, **kwargs):
        payment = get_draft(request)
        if not payment:
            raise NotFound({'detail': 'draft not found'})

        payment.status = PAYMENT_STATUSES[1]
        payment.save()
        return Response(PaymentSerializer(payment).data)


# Donation inside draft managing:
class PaymentDonationView(APIView):
    permission_classes = [IsUser]

    def _sum_without_overflow(self, obj: Work, sum):
        def count_sum(given, already_given, total):
            remaining_total = total - already_given
            sum = remaining_total if given > remaining_total else given
            if not sum:
                raise ValidationError({'detail': 'This work already got enough donations..'})
            return sum

        already_given = obj.donation_set.exclude(
            payment__status=PAYMENT_STATUSES[-1], payment__date_close=None
        ).aggregate(sum=Sum('sum'))['sum'] or 0
        total = obj.sum
        return count_sum(sum, already_given, total)

    def put(self, request, *args, **kwargs):
        payment = get_draft(request)
        work = get_model_obj(Work, request.data.get('work_id'))

        sum = request.data.get('sum')
        if not sum or sum < 0:
            raise ValidationError({'detail': 'sum field is incorrect or not applied'})

        # Creating draft if needed:
        if not payment:
            payment = Payment.objects.create(user=request.user)

        # Guard checks:
        if work.status == WORK_STATUSES[-1] or \
                work.restore.status in [RESTORATION_STATUSES[0], RESTORATION_STATUSES[-1]]:
            raise PermissionDenied({'detail': 'this work or restoration status doesnt allow to donate money'})

        # Adding donation to this work if not already added:
        existing_donation = payment.donation_set.filter(work=work).first()
        if not existing_donation:
            sum = self._sum_without_overflow(work, sum)
            payment.donation_set.create(work=work, sum=sum)
        else:
            sum = self._sum_without_overflow(existing_donation.work, sum)
            existing_donation.sum = sum
            existing_donation.save()

        return Response(PaymentSerializer(payment, context={'request': request}).data)

    def delete(self, request, *args, **kwargs):
        payment = get_draft(request)
        if not payment:
            raise NotFound({'detail': 'draft not found'})

        work = get_model_obj(Work, request.data.get('work_id'), force_empty=True)
        if work:
            donation = payment.donation_set.filter(work=work.id).first()
            if donation:
                donation.delete()

        return Response(PaymentSerializer(payment, context={'request': request}).data)


@method_decorator(csrf_exempt, name='post')
class AsincServiceMount(APIView):
    def post(self, request, *args, **kwargs):
        payment_id = request.data.get('id')
        if not payment_id:
            raise ValidationError({'detail': 'id field not specified'})

        secrey_key = request.data.get('key')
        if not secrey_key or secrey_key != WEB_SERVICE_SEKRET_KEY:
            raise PermissionDenied({'detail': 'key field not applied or not correct'})

        status = request.data.get('status')
        if not status or status not in PAYMENT_STATUSES:
            raise ValidationError({'detail': 'status field not specified or is wrong'})

        payment = Payment.objects.filter(pk=payment_id).first()
        if not payment:
            raise NotFound({'detail': 'such payment not found'})

        payment.status = status
        payment.save()
        return Response(PaymentSerializer(payment).data)
