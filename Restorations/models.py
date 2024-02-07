from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from Restorations.validators import *

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.timezone import now
from hashlib import sha256


class Restoration(models.Model):
    name = models.CharField(max_length=70)
    image = models.ImageField(blank=True, null=True)
    description = models.TextField()
    status = models.CharField(
        max_length=9, blank=True,
        validators=[restoration_status_validate],
        default=list(RESTORATION_STATUSES.keys())[0],
        choices=[(key, value) for key, value in RESTORATION_STATUSES.items()]
    )
    banck_account = models.CharField(max_length=12)

    class Meta:
        managed = True
        db_table = 'Restorations'

    def __str__(self):
        return ''


class Work(models.Model):
    restore = models.ForeignKey(Restoration, models.CASCADE)
    name = models.CharField(max_length=100)
    sum = models.FloatField(validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10, blank=True,
        validators=[work_status_validate],
        default=list(WORK_STATUSES.keys())[0],
        choices=[(key, value) for key, value in WORK_STATUSES.items()]
    )

    class Meta:
        managed = True
        db_table = 'Works'

    def __str__(self):
        return self.name


class Payment(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    manager = models.ForeignKey(User, models.SET_NULL,
                                related_name='payment_from_manager_set', blank=True, null=True,
                                editable=False)
    code = models.CharField(max_length=10, blank=True, null=False, editable=False)
    status = models.CharField(
        max_length=9,
        blank=True,
        default=list(PAYMENT_STATUSES.keys())[0],
        validators=[payment_status_validate],
        choices=[(key, value) for key, value in PAYMENT_STATUSES.items()]
    )
    date_open = models.DateField(auto_now=True)
    date_pay = models.DateField(blank=True, null=True)
    date_close = models.DateField(blank=True, null=True, editable=False)

    class Meta:
        managed = True
        db_table = 'Payments'

    def __str__(self):
        return ''


class Donation(models.Model):
    payment = models.ForeignKey(Payment, models.CASCADE)
    work = models.ForeignKey(Work, models.CASCADE)
    sum = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        managed = True
        db_table = "Donations"


@receiver(post_save, sender=Payment)
def save_payment(sender, instance, *args, **kwargs):  # Could be made inside by usual create
    id = instance.id
    payment = Payment.objects.filter(id=id)

    # Setting date_close and date_pay after status fixing:
    date_close = now().date() \
        if instance.status in (PAYMENT_STATUSES[-2], PAYMENT_STATUSES[-3]) \
        else None
    date_pay = now().date() if instance.status == 'Paid' else None

    if not payment.first().date_pay and date_pay:
        instance.date_pay = date_pay
        payment.update(date_pay=date_pay)

    if not payment.first().date_close and date_close:
        instance.date_close = date_close
        payment.update(date_close=date_close)

    # Setting payment code:
    if not instance.code:
        code = sha256(str(id).encode('utf-8')).hexdigest()[:10]
        payment.update(code=code)
        instance.code = code