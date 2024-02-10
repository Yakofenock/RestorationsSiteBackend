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
    can_delete = False

    def restoration(self, instance):
        return instance.work.restore.name

    def has_add_permission(self, *args):
        return False

    def has_change_permission(self, *args):
        return False


class PaymentView(admin.ModelAdmin):
    inlines = [DonationInline]
    list_display = ['user', 'status', 'code', 'sum', 'date_open', 'date_pay', 'date_close']
    search_fields = ['user__username', 'status',  'date_open']
    readonly_fields = ['code', 'sum', 'manager', 'date_open', 'date_close', 'user', 'date_pay']

    def sum(self, obj):
        return obj.donation_set.aggregate(Sum('sum'))['sum__sum'] or 0

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.manager = request.user
        obj.save()


admin.site.register(Restoration, RestorationView)
admin.site.register(Payment, PaymentView)
