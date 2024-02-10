from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (ModelSerializer,
                                        SerializerMethodField,
                                        PrimaryKeyRelatedField,
                                        IntegerField)
from Restorations.models import Restoration, Work, Payment, Donation, User
from Restorations.utils import PAYMENT_STATUSES
from django.db.models import Sum, Q
from Restorations.utils import count_percent, short_field


class WorkSerialiser(ModelSerializer):
    given_sum = SerializerMethodField()
    total_sum = IntegerField(source='sum')
    # restore = Foo(read_only=True, source='restore__id')

    def get_given_sum(self, obj):
        return obj.donation_set.filter(
            Q(payment__status=PAYMENT_STATUSES[-2]) |
            (Q(payment__status=PAYMENT_STATUSES[-1]) & Q(payment__date_close=None))
        ).aggregate(sum=Sum('sum'))['sum'] or 0

    def validate_total_sum(self, obj):
        if obj <= 0:
            raise ValidationError({'detail': 'total_sum field is incorrect ..'})
        return obj

    def __init__(self, *args, **kwargs):
        super(WorkSerialiser, self).__init__(*args, **kwargs)
        if self.context.get('request'):
            print(self.context['request'].method in ['POST', 'PUT'])
            if self.context['request'].method not in ['POST']:
                self.fields.pop('restore')
                ...

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context['request'].method in ['PUT']:
            data['restore'] = instance.restore.id
        return data

    class Meta:
        model = Work
        fields = ['id', 'name', 'restore', 'given_sum', 'total_sum', 'status']


# Used to prepare a data structures which will be grouped by user:
class DonaterDonationSerialiser(ModelSerializer):
    name = SerializerMethodField()
    work_id = SerializerMethodField()
    work = SerializerMethodField()
    given_sum = SerializerMethodField()
    percent = SerializerMethodField()

    def get_name(self, obj):
        return obj.payment.user.username

    def get_work_id(self, obj):
        return obj.work.pk

    def get_work(self, obj):
        return obj.work.name

    def get_given_sum(self, obj):
        return obj.sum

    def get_percent(self, obj):
        return count_percent(obj.sum, obj.work.sum)

    class Meta:
        model = Donation
        fields = ['name', 'work_id', 'work', 'given_sum', 'percent']


def StackByDonater(donater_donations):
    stacked_donaters = []
    donaters_indexes = {}

    for donation in donater_donations:
        name = donation['name']

        # Creating new user stack:
        if name not in donaters_indexes:
            total_restore_sum = Work.objects.filter(
                restore=Restoration.objects.filter(work__pk=donation['work_id']).first()
            ).aggregate(sum=Sum('sum'))['sum'] or 0

            donaters_indexes[name] = len(stacked_donaters)
            stacked_donaters.append(dict(name=name, works=[], given_sum=0,
                                         total_sum=total_restore_sum))

        # Adding info:
        index = donaters_indexes[name]
        stacked_donaters[index]['works'].append(
            dict(work_id=donation['work_id'], work=donation['work'],
                 given_sum=donation['given_sum'], percent=donation['percent'])
        )

        # Counting global given_sum for restoration:
        stacked_donaters[index]['given_sum'] += donation['given_sum']

    # Counting global percentage:
    for donation in stacked_donaters:
        donation.update({'percent': count_percent(donation['given_sum'],
                                                  donation['total_sum'])})
        donation.pop('total_sum')

    return stacked_donaters


class RestorationSerialiser(ModelSerializer):
    given_sum = SerializerMethodField()
    total_sum = SerializerMethodField()
    donaters = SerializerMethodField()

    # def get_given_sum(self, obj):
    #     return Donation.objects.filter(
    #         work__restore__pk=obj.pk,
    #         payment__status=PAYMENT_STATUSES[-2]).aggregate(sum=Sum('sum'))['sum'] or 0

    def get_given_sum(self, obj):
        return Donation.objects.filter(
            Q(work__restore__pk=obj.pk) &
            (
                    Q(payment__status=PAYMENT_STATUSES[-2]) |
                    (Q(payment__status=PAYMENT_STATUSES[-1]) & Q(payment__date_close=None))
            )
        ).aggregate(sum=Sum('sum'))['sum'] or 0

    def get_total_sum(self, obj):
        return obj.work_set.aggregate(sum=Sum('sum'))['sum'] or 0

    def get_donaters(self, obj):
        return StackByDonater(
            DonaterDonationSerialiser(
                many=True,
                instance=Donation.objects.filter(
                    work__restore=obj, payment__status=PAYMENT_STATUSES[-2]
                ),
                read_only=True
            ).data
        )

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if self.short_variant:
            data['description'] = short_field(data['description'])
        return data

    def __init__(self, *args, **kwargs):
        self.short_variant = kwargs.pop('short_variant', False)
        super(RestorationSerialiser, self).__init__(*args, **kwargs)

        # While project building object context is empty and serializer obj is created for testing:
        request = self.context.get('request')
        specific = self.context.get('specific')
        if request or specific:
            dict = request.resolver_match.url_name if request else []
            if 'detail' in dict or specific:
                self.fields['works'] = WorkSerialiser(many=True, source='work_set', read_only=True)
            else:
                self.fields.pop('donaters')

            self.short_variant = self.short_variant or 'list' in dict

    class Meta:
        model = Restoration
        fields = ['id', 'name', 'image', 'status', 'description', 'given_sum', 'total_sum', 'donaters']


class DonationSerialiser(ModelSerializer):
    work_id = SerializerMethodField()
    restore_id = SerializerMethodField()
    restore_name = SerializerMethodField()
    restore_bank = SerializerMethodField()
    work = SerializerMethodField()
    given_sum = IntegerField(source='sum')
    total_sum = SerializerMethodField()
    percent = SerializerMethodField()

    def get_work_id(self, obj):
        return obj.work.pk

    def get_restore_id(self, obj):
        return obj.work.restore.pk

    def get_restore_name(self, obj):
        return obj.work.restore.name

    def get_restore_bank(self, obj):
        return obj.work.restore.banck_account

    def get_total_sum(self, obj):
        return obj.work.sum

    def get_work(self, obj):
        return obj.work.name

    def get_percent(self, obj):
        return count_percent(
            obj.sum,
            obj.work.sum
        )

    class Meta:
        model = Donation
        fields = ['work_id', 'restore_id', 'restore_name', 'restore_bank',  'work', 'given_sum', 'total_sum', 'percent']


class PaymentSerializer(ModelSerializer):
    given_sum = SerializerMethodField()
    # donations = PrimaryKeyRelatedField(many=True, source='donation_set', read_only=True)

    donations = SerializerMethodField()

    def get_donations(self, obj):
        return [donation.work.pk for donation in obj.donation_set.all()]

    def get_given_sum(self, obj):
        return sum(donation.sum for donation in obj.donation_set.all())

    def __init__(self, *args, **kwargs):
        super(PaymentSerializer, self).__init__(*args, **kwargs)
        if self.context.get('request'):
            dict = self.context['request'].resolver_match.url_name
            if (self.context['request'].method in ['DELETE', 'PUT']) or (dict and 'detail' in dict):
                self.fields['donations'] = DonationSerialiser(many=True,  source='donation_set')

    class Meta:
        model = Payment
        read_only_fields = ['date_open', 'donations', 'date_close',  'user', 'code']
        fields = '__all__'
