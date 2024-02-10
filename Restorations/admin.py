from django.contrib import admin
from django.db.models import Sum
from .models import Restoration, Work, Payment, Donation


# Supplies:
class WorkInline(admin.StackedInline):
    model = Work
    extra = 0
    readonly_fields = ['sum']

    def got_sum(self, obj):
        return obj.donation_set.aggregate(Sum('sum'))['sum__sum'] or 0


class RestorationView(admin.ModelAdmin):
    inlines = [WorkInline]
    list_display = ['name', 'status', 'given_sum', 'total_sum']
    readonly_fields = ['total_sum', 'given_sum']

    def given_sum(self, obj):
        return obj.work_set.aggregate(Sum('donation__sum'))['donation__sum__sum'] or 0

    def total_sum(self, obj):
        return obj.work_set.aggregate(Sum('sum'))['sum__sum'] or 0


# Payments:
class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0
    readonly_fields = ['restoration']

    def restoration(self, instance):
        return instance.work.restore.name


class PaymentView(admin.ModelAdmin):
    inlines = [DonationInline]
    list_display = ['user', 'status', 'code', 'sum', 'date_open', 'date_pay', 'date_close']
    search_fields = ['user__username', 'status',  'date_open']
    readonly_fields = ['code', 'sum', 'manager', 'date_open', 'date_close']

    def sum(self, obj):
        return obj.donation_set.aggregate(Sum('sum'))['sum__sum'] or 0


admin.site.register(Restoration, RestorationView)
admin.site.register(Payment, PaymentView)
