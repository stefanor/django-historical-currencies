import xml.etree.ElementTree as ET
from urllib.request import urlopen

from django.core.management.base import BaseCommand, CommandError

from historical_currencies.models import ExchangeRate

NAMESPACE = {
    "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
    "gesmes": "http://www.gesmes.org/xml/2002-08-01",
}


class Command(BaseCommand):
    help = "Import daily or historical exchange rate data from the ECB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            metavar="URL",
            help="Load from a custom URL",
        )
        parser.add_argument(
            "--daily",
            dest="url",
            action="store_const",
            const="https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
            help="Load the daily exchange rates",
        )
        parser.add_argument(
            "--historical",
            dest="url",
            action="store_const",
            const="https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
            help="Load the full set of historical exchange rates",
        )

    def iter_rates(self, url):
        with urlopen(url) as f:
            data = ET.parse(f)
        root = data.getroot()
        for day in root.iterfind("./eurofxref:Cube/eurofxref:Cube[@time]", NAMESPACE):
            date = day.get("time")
            for rate in day.iterfind("eurofxref:Cube", NAMESPACE):
                currency = rate.get("currency")
                exchange_rate = rate.get("rate")
                yield ExchangeRate(
                    date=date,
                    base_currency="EUR",
                    currency=currency,
                    rate=exchange_rate,
                )

    def handle(self, *args, **options):
        if not options["url"]:
            raise CommandError(
                "A URL must be provided with --daily, --historical, or --url"
            )
        ExchangeRate.objects.bulk_create(
            self.iter_rates(options["url"]),
            ignore_conflicts=True,
        )
