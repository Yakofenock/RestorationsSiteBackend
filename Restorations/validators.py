from django.core.validators import ValidationError


payments_statuses = {'Opened': 'Формируется',
                    'Paid': 'Оплачена',
                    'Rejected': 'Отклонена',
                    'Completed': 'Принята',
                    'Deleted': 'Удалена',
                    }


def payment_status_validate(value):
    if value not in payments_statuses.keys():
        raise ValidationError(f'Status shoulde be one of {payments_statuses.keys()}')


restoration_statuses = {'Forming': 'Формируется', 'InProcess': 'В процессе', 'Completed': 'Завершена'}


def restoration_status_validate(value):
    if value not in restoration_statuses.keys():
        raise ValidationError(f'Restoration status should be one of {restoration_statuses.keys()}')


work_statuses = {'NotStarted': 'Не начата', 'InProcess': 'В процессе', 'Completed': 'Завершена'}


def work_status_validate(value):
    if value not in work_statuses.keys():
        raise ValidationError(f'Work status should be one of {work_statuses.keys()}')