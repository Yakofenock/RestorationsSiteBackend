from django import template
from Site.settings import MONEY_SYMBOL, DIGITS_RU_NAMES
register = template.Library()


@register.filter(name='display_int')
def display_int(value, lamg='ru'):
    if value:
        value = int(value)
        for check in [1_000_000_000, 1_000_000, 1_000]:
            if value >= check:
                whole, remains = divmod(value, check)
                if len(str(remains)) <= 2:
                    return f"{whole} {DIGITS_RU_NAMES[check]}"
    return value