import json
from datetime import date, timedelta
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from historical_currencies.models import ExchangeRate


class Command(BaseCommand):
    help = "Import daily or historical exchange rate data from OpenExchangeRates.org"

    def add_arguments(self, parser):
        daterange = parser.add_mutually_exclusive_group()
        daterange.add_argument(
            "--yesterday",
            action="store_true",
            help="Load yesterday's daily exchange rates",
        )
        daterange.add_argument(
            "--update",
            action="store_true",
            help="Load exchange rates since the latest in the database",
        )
        daterange.add_argument(
            "--since",
            metavar="DATE",
            type=parse_date,
            help="Load exchange rates since DATE",
        )
        daterange.add_argument(
            "--date",
            metavar="DATE",
            type=parse_date,
            help="Load exchange rates for DATE (only)",
        )

    def iter_month_ranges(self, start_date, end_date):
        month_start = start_date
        month_end = month_start + timedelta(days=31)
        while month_end < end_date:
            yield (month_start, month_end)
            month_start = month_end + timedelta(days=1)
            month_end = month_start + timedelta(days=31)
        yield (month_start, end_date)

    def iter_days(self, start_date, end_date):
        day = start_date
        while day <= end_date:
            yield day
            day += timedelta(days=1)

    def oxr_request(self, endpoint, query=None):
        if query is None:
            query = {}
        query["app_id"] = settings.OPEN_EXCHANGE_RATES_APP_ID
        url = urlunparse(
            (
                "https",
                "openexchangerates.org",
                f"api/{endpoint}",
                None,
                urlencode(query),
                None,
            )
        )
        with urlopen(url) as f:
            if f.status != 200:
                raise Exception("Request failed")
            return json.load(f)

    def check_usage(self, start_date, end_date):
        usage = self.oxr_request("usage.json")["data"]
        self.plan = usage["plan"]
        requests_remaining = usage["usage"]["requests_remaining"]
        days_to_query = (end_date - start_date).days
        if days_to_query > requests_remaining:
            raise Exception(
                f"Insufficient quota: days: {days_to_query}, "
                f"requests remaining: {requests_remaining}"
            )
        if (
            not self.plan["features"]["base"]
            and settings.OPEN_EXCHANGE_RATES_BASE_CURRENCY != "USD"
        ):
            raise Exception(
                "OpenExchangeRates plan doesn't support non-USD " "base currency"
            )

    def iter_historical_rates(self, day):
        rates = self.oxr_request(
            f"historical/{day.isoformat()}.json",
            {
                "base": settings.OPEN_EXCHANGE_RATES_BASE_CURRENCY,
            },
        )
        for currency, rate in rates["rates"].items():
            yield ExchangeRate(
                date=day,
                base_currency=rates["base"],
                currency=currency,
                rate=rate,
            )

    def iter_time_series_rates(self, start_date, end_date):
        historic_rates = self.oxr_request(
            "time-series.json",
            {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "base": settings.OPEN_EXCHANGE_RATES_BASE_CURRENCY,
            },
        )
        # FIXME: Untested
        for day, rates in historic_rates["rates"].items():
            for currency, rate in rates.items():
                yield ExchangeRate(
                    date=day,
                    base_currency=rates["base"],
                    currency=currency,
                    rate=rate,
                )

    def handle(self, *args, **options):
        yesterday = date.today() - timedelta(days=1)
        if options["yesterday"]:
            daterange = (yesterday, yesterday)
        elif options["update"]:
            latest = ExchangeRate.objects.all().order_by("-date").first()
            if latest.date >= yesterday:
                print("Already up to date")
                return
            daterange = (latest.date + timedelta(days=1), yesterday)
        elif options["since"]:
            daterange = (options["since"], yesterday)
        elif options["date"]:
            daterange = (options["date"], options["date"])
        else:
            raise CommandError("No date range specified")

        self.check_usage(*daterange)
        if self.plan["features"]["time-series"]:
            for month_range in self.iter_month_ranges(*daterange):
                ExchangeRate.objects.bulk_create(
                    self.iter_time_series_rates(*month_range),
                    ignore_conflicts=True,
                )
        else:
            for day in self.iter_days(*daterange):
                ExchangeRate.objects.bulk_create(
                    self.iter_historical_rates(day),
                    ignore_conflicts=True,
                )
