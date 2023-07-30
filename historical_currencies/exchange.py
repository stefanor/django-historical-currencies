import datetime
from functools import lru_cache
from decimal import Decimal
from typing import Iterator, List, Optional, Tuple

from django.db.models import Q
from django.conf import settings

from historical_currencies.exceptions import ExchangeRateUnavailable
from historical_currencies.models import ExchangeRate

TWOPLACES = Decimal(10) ** -2

try:
    from functools import cache
except ImportError:  # Python < 3.9
    cache = lru_cache(maxsize=None)


@lru_cache()
def latest_rate(
    currency_from: str,
    currency_to: str,
    date: datetime.date,
) -> (datetime.date, Decimal):
    """The latest exchange rate from currency_from to currency_to as of date.

    currency_from and currency_to must have a direct conversion available
    """
    rates = list(_iter_available_rates(currency_from, currency_to, date))
    rates.sort(reverse=True)
    if not rates:
        raise ExchangeRateUnavailable(
            f"No exchange rate available between {currency_from} and {currency_to} for {date}"
        )
    return rates[0]


@cache
def _possible_base_currencies() -> List[str]:
    return [
        rate["base_currency"]
        for rate in ExchangeRate.objects.values("base_currency").distinct()
    ]


def _iter_available_rates(
    currency_from: str,
    currency_to: str,
    date: datetime.date,
) -> Iterator[Tuple[datetime.date, Decimal]]:
    """Helper to find the latest exchange rate from currency_from to
    currency_to as of date.

    Look for direct conversion, or indirect conversion via a single base
    currency. Yield all the combinations we found.
    """
    oldest_acceptable_rate = date - datetime.timedelta(
        days=settings.MAX_EXCHANGE_RATE_AGE
    )

    direct_rate = (
        ExchangeRate.objects.filter(date__lte=date, date__gte=oldest_acceptable_rate)
        .filter(
            Q(currency=currency_from, base_currency=currency_to)
            | Q(currency=currency_to, base_currency=currency_from)
        )
        .order_by("-date")
        .first()
    )
    if direct_rate:
        rate = direct_rate.rate
        if direct_rate.base_currency == currency_to:
            rate = 1 / rate
        yield direct_rate.date, rate

    for base_currency in _possible_base_currencies():
        rate_date = None
        rate_from = None
        rate_to = None
        for rate in (
            ExchangeRate.objects.filter(
                date__lte=date, date__gte=oldest_acceptable_rate
            )
            .filter(
                Q(currency=currency_from, base_currency=base_currency)
                | Q(currency=currency_to, base_currency=base_currency)
            )
            .order_by("-date")
        ):
            if rate_date != rate.date:
                rate_date = rate.date
                rate_from = rate.rate if rate.currency == currency_from else None
                rate_to = rate.rate if rate.currency == currency_to else None
            elif rate.currency == currency_from and rate_to is not None:
                rate_from = rate.rate
                yield rate_date, rate_to / rate_from
                continue
            elif rate.currency == currency_to and rate_from is not None:
                rate_to = rate.rate
                yield rate_date, rate_to / rate_from
                continue


def exchange(
    amount: Decimal,
    currency_from: str,
    currency_to: str,
    date: Optional[datetime.date] = None,
) -> Decimal:
    """Exchange amount of currency_from to currency_to as of date"""
    if date is None:
        date = datetime.date.today()

    if currency_from == currency_to:
        rate_date = date
        rate = Decimal(1)
    else:
        rate_date, rate = latest_rate(currency_from, currency_to, date)

    amount *= rate
    if date - rate_date > datetime.timedelta(days=settings.MAX_EXCHANGE_RATE_AGE):
        raise ExchangeRateUnavailable(
            f"The last available rate for {currency_from}:{currency_to} before "
            f"{date} is {rate_date} which is too old"
        )

    return amount.quantize(TWOPLACES)
