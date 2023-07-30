import datetime
from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase, TestCase

from historical_currencies.models import ExchangeRate


def render_template(body, context, load_currency_format=True):
    if isinstance(context, dict):
        context = Context(context)
    if load_currency_format:
        body = "{% load currency_format %}" + body
    return Template(body).render(context)


class CurrencyTagTestCase(SimpleTestCase):
    def test_currency_filter(self):
        rendered = render_template("{{ ben|currency }}", {"ben": (Decimal(100), "USD")})
        self.assertEqual(rendered, "100.00 USD")


class ExchangeRateTagTestCase(TestCase):
    def test_exchange_filter_with_rate(self):
        date = datetime.date.today()
        ExchangeRate.objects.create(
            date=date, base_currency="EUR", currency="USD", rate=1.1326
        )
        rendered = render_template(
            "{{ eur|exchange:'USD' }}", {"eur": (Decimal(1), "EUR")}
        )
        self.assertEqual(rendered, "1.13 USD")

    def test_exchange_filter_missing_rate(self):
        with self.assertLogs(
            "historical_currencies.templatetags.currency_format",
            level="WARNING",
        ) as cm:
            rendered = render_template(
                "{{ eur|exchange:'USD' }}", {"eur": (Decimal(1), "EUR")}
            )
        self.assertEqual(rendered, "? (no rate) USD")
        self.assertEqual(len(cm.records), 1)
        log = cm.records[0]
        self.assertEqual(log.message, "Missing Exchange Rate: EUR:USD")
