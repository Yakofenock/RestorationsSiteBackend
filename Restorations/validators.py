from django.core.validators import ValidationError


PAYMENT_STATUSES = {'Opened': 'Формируется',
                    'Paid': 'Оплачена',
                    'Rejected': 'Отклонена',
                    'Completed': 'Принята',
                    'Deleted': 'Удалена',
                    }


def payment_status_validate(value):
    if value not in PAYMENT_STATUSES.keys():
        raise ValidationError(f'Status shoulde be one of {PAYMENT_STATUSES.keys()}')


RESTORATION_STATUSES = {'Forming': 'Формируется', 'InProcess': 'В процессе', 'Completed': 'Завершена'}


def restoration_status_validate(value):
    if value not in RESTORATION_STATUSES.keys():
        raise ValidationError(f'Restoration status should be one of {RESTORATION_STATUSES.keys()}')


WORK_STATUSES = {'NotStarted': 'Не начата', 'InProcess': 'В процессе', 'Completed': 'Завершена'}


def work_status_validate(value):
    if value not in WORK_STATUSES.keys():
        raise ValidationError(f'Work status should be one of {WORK_STATUSES.keys()}')