from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from Restorations.models import Restoration, Work, Payment, Donation
from django.db.models import Q, Sum

from .serialisers import RestorationSerialiser, PaymentSerializer, WorkSerialiser
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound, MethodNotAllowed
from Restorations.utils import RESTORATION_STATUSES, WORK_STATUSES, PAYMENT_STATUSES
from datetime import datetime

from ..user_singleton import UserSingleton


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
    return Payment.objects.filter(user=UserSingleton(),
                                  status=PAYMENT_STATUSES[0]).first()


class RestorationViewSet(ModelViewSet):
    serializer_class = RestorationSerialiser
    queryset = Restoration.objects.none()
    http_method_names = ['get', 'post', 'delete', 'put']

    def get_queryset(self):
        soft = Restoration.objects.all().filter(status=RESTORATION_STATUSES[0])

        # Processing search:
        search = self.request.GET.get('search')
        if search:
            soft = soft.filter(
                Q(name__icontains=search) | Q(description__icontains=search) |
                Q(work__name__icontains=search)
            ).distinct()  # Last query can put few same result

        return soft

    def list(self, request: Request, *args, **kwargs):
        result = add_count_option(self, request)
        if result:
            return result

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

    def get_queryset(self):
        payments = Payment.objects.all().exclude(status__in=[PAYMENT_STATUSES[0],
                                                             PAYMENT_STATUSES[-1]])

        # Viewing of all list protection from user:
        user = UserSingleton()
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
                'today_requested': #??
                    self.get_queryset().aggregate(summ_req=Sum('work__donation__sum'))['summ_req']
            })

        return super().list(request, args, kwargs)

    def retrieve(self, request, *args, **kwargs):
        payment = get_model_obj(Payment, kwargs.get('pk'))  # Because get_queryset takes opened away
        if payment.status == PAYMENT_STATUSES[-1]:
            raise NotFound({'detail': 'payment not found'})

        if payment.user != UserSingleton():
            raise PermissionDenied()

        return Response(self.get_serializer(payment).data)

    def destroy(self, request: Request, *args, **kwargs):
        payment = get_model_obj(Payment, kwargs.get('pk'))  # Same

        # Not to allow to user to delete other users payments:
        if payment.user != UserSingleton():
            raise PermissionDenied()

        if payment.status == PAYMENT_STATUSES[-1]:
            raise NotFound({'detail': 'this payment already deleted'})

        payment.status = PAYMENT_STATUSES[-1]
        payment.save()
        return Response(status=204)


# Manging status of payment for admin:
class PaymentStatusAdminView(APIView):

    def put(self, request, *args, **kwargs):
        payment = get_model_obj(Payment, kwargs.get('pk'))

        if payment.status == PAYMENT_STATUSES[-1]:
            raise NotFound({'detail': 'there is no such payment'})

        if payment.status != PAYMENT_STATUSES[1]:
            raise PermissionDenied({'detail': 'you cant change status now'})

        status = request.data.get('status')
        if status not in [PAYMENT_STATUSES[-3], PAYMENT_STATUSES[-2]]:
            raise PermissionDenied({'detail': 'wrong status specified'})

        payment.manager = UserSingleton()
        payment.status = status
        payment.save()

        return Response(PaymentSerializer(payment).data)


# Manging status of payment for user:
class PaymentStatusUserView(APIView):

    def put(self, request, *args, **kwargs):
        payment = get_draft(request)
        if not payment:
            raise NotFound({'detail': 'draft not found'})

        payment.status = PAYMENT_STATUSES[1]
        payment.save()
        return Response(PaymentSerializer(payment).data)


# Soft inside draft managing:
class PaymentDonationView(APIView):
    def put(self, request, *args, **kwargs):
        payment = get_draft(request)
        work = get_model_obj(Work, request.data.get('work'))

        sum = request.data.get('sum')
        if not sum:
            raise ValidationError({'detail': 'sum field is incorrect or not applied'})

        # Creating draft if needed:
        if not payment:
            payment = Payment.objects.create(user=UserSingleton())

        # Adding soft if not already added:
        existing_work = payment.donation_set.filter(work=work).first()
        if not existing_work:
            payment.donation_set.create(work=work, sum=sum)
        else:
            existing_work.sum = sum
            existing_work.save()

        return Response(PaymentSerializer(payment, context={'request': request}).data)

    def delete(self, request, *args, **kwargs):
        payment = get_draft(request)
        if not payment:
            raise NotFound({'detail': 'draft not found'})

        work = get_model_obj(Work, request.data.get('work'), force_empty=True)
        if work:
            payment.donation_set.filter(work=work.id).first().delete()

        return Response(PaymentSerializer(payment, context={'request': request}).data)