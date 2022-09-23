import datetime
from decimal import Decimal

from currencies.models import ExchangeRate

TWOPLACES = Decimal(10) ** -2


def exchange(
    amount: Decimal, currency_from: str, currency_to: str, date: datetime.date
) -> Decimal:
    """Exchange amount of currency_from to currency_to as of date"""
    # Currency amount is represented in
    currency = currency_from

    last_rate = ExchangeRate.objects.filter(date__lte=date).order_by("-date").first()
    # Assumption: all relevent currencies present every day
    last_date = last_rate.date
    # Assumption: all currencies use a common base_currency
    last_base = last_rate.base_currency

    if currency_from != last_base:
        rate = ExchangeRate.objects.get(
            currency=currency, base_currency=last_base, date=last_date
        )
        amount /= rate.rate
        currency = last_base

    if currency != currency_to:
        rate = ExchangeRate.objects.get(
            currency=currency_to, base_currency=currency, date=last_date
        )
        amount *= rate.rate
        currency = last_base

    return amount.quantize(TWOPLACES)
