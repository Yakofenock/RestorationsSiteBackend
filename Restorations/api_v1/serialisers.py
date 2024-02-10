from rest_framework.serializers import (ModelSerializer,
                                        SerializerMethodField,
                                        IntegerField)
from Restorations.models import Restoration, Work, Payment, Donation, User
from django.db.models import Sum
from Restorations.utils import count_percent, short_field


class WorkSerialiser(ModelSerializer):
    given_sum = SerializerMethodField()
    total_sum = IntegerField(source='sum')

    def get_given_sum(self, obj):
        return obj.donation_set.aggregate(sum=Sum('sum'))['sum'] or 0

    def __init__(self, *args, **kwargs):
        super(WorkSerialiser, self).__init__(*args, **kwargs)
        if self.context.get('request'):
            if 'work-list' not in self.context['request'].resolver_match.url_name:
                self.fields.pop('restore')

    class Meta:
        model = Work
        fields = ['id', 'restore', 'name', 'given_sum', 'total_sum']


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
            print(total_restore_sum)

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

    return stacked_donaters


class RestorationSerialiser(ModelSerializer):
    given_sum = SerializerMethodField()
    total_sum = SerializerMethodField()
    donaters = SerializerMethodField()

    def get_given_sum(self, obj):
        return obj.work_set.aggregate(sum=Sum('donation__sum'))['sum'] or 0

    def get_total_sum(self, obj):
        return obj.work_set.aggregate(sum=Sum('sum'))['sum'] or 0

    def get_donaters(self, obj):
        return StackByDonater(
            DonaterDonationSerialiser(
                many=True,
                instance=Donation.objects.filter(work__restore=obj),
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
        if self.context.get('request'):
            dict = self.context['request'].resolver_match.url_name
            if 'detail' in dict:
                self.fields['works'] = WorkSerialiser(many=True, source='work_set', read_only=True)
            else:
                self.fields.pop('donaters')

            self.short_variant = self.short_variant or 'list' in dict

    class Meta:
        model = Restoration
        fields = ['id', 'name', 'image', 'description', 'given_sum', 'total_sum', 'donaters']


class DonationSerialiser(ModelSerializer):
    work_id = SerializerMethodField()
    work = SerializerMethodField()
    given_sum = IntegerField(source='sum')
    percent = SerializerMethodField()

    def get_work_id(self, obj):
        return obj.work.pk

    def get_work(self, obj):
        return obj.work.name

    def get_percent(self, obj):
        return count_percent(
            obj.work.donation_set.aggregate(sum=Sum('sum'))['sum'] or 0,
            obj.work.sum
        )

    class Meta:
        model = Donation
        fields = ['work_id', 'work', 'given_sum', 'percent']


class PaymentSerializer(ModelSerializer):
    given_sum = SerializerMethodField()

    def get_given_sum(self, obj):
        return sum(donation.sum for donation in obj.donation_set.all())

    def __init__(self, *args, **kwargs):
        super(PaymentSerializer, self).__init__(*args, **kwargs)
        if self.context.get('request'):
            dict = self.context['request'].resolver_match.url_name
            if (self.context['request'].method in ['DELETE', 'PUT']) or (dict and 'detail' in dict):
                self.fields['donations'] = DonationSerialiser(many=True, source='donation_set', read_only=True)

    class Meta:
        model = Payment
        read_only_fields = ['date_open', 'date_close',  'user', 'code']
        fields = '__all__'
