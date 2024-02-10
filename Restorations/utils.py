from Site.settings import ROUND
from Restorations.validators import restoration_statuses, work_statuses, payments_statuses


def count_percent(val1, val2):
    return round(val1/val2*100, ROUND) if val2 else 0


def short_field(value):
    return value[:100] + ('...' if len(value) > 100 else '')


RESTORATION_STATUSES = list(restoration_statuses.keys())
WORK_STATUSES = list(work_statuses.keys())
PAYMENT_STATUSES = list(payments_statuses.keys())
