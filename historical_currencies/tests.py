import datetime
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, tag

import historical_currencies.exchange  # imported for mock patching # noqa: F401
from historical_currencies.choices import currency_choices
from historical_currencies.exceptions import ExchangeRateUnavailable
from historical_currencies.exchange import exchange, latest_rate, _possible_base_currencies
from historical_currencies.formatting import render_amount
from historical_currencies.models import ExchangeRate, check_fresh_exchange_rate_data


class ExchangeRateObjectTestCase(SimpleTestCase):
    def test_str_method(self):
        er = ExchangeRate(
            date=datetime.date(2021, 12, 31),
            base_currency="EUR",
            currency="USD",
            rate=1.1326,
        )
        self.assertEqual(str(er), "Exchange Rate: EUR-USD @ 2021-12-31: 1.1326")


class SimpleExchangeTestCase(TestCase):
    date = datetime.date(2021, 12, 31)

    def setUp(self):
        latest_rate.cache_clear()
        _possible_base_currencies.cache_clear()
        ExchangeRate.objects.create(
            date=self.date, base_currency="EUR", currency="USD", rate=1.1326
        )
        ExchangeRate.objects.create(
            date=self.date, base_currency="EUR", currency="ZAR", rate=18.0625
        )

    def test_can_noop_exchange(self):
        self.assertEqual(exchange(1, "EUR", "EUR", date=self.date), Decimal("1"))

    def test_can_exchange_from_base(self):
        self.assertEqual(exchange(1, "EUR", "USD", date=self.date), Decimal("1.13"))

    def test_can_exchange_to_base(self):
        self.assertEqual(exchange(1, "USD", "EUR", date=self.date), Decimal("0.88"))

    def test_can_exchange_through_base(self):
        self.assertEqual(exchange(1, "USD", "ZAR", date=self.date), Decimal("15.95"))

    def test_uses_last_valid_rate(self):
        self.assertEqual(
            exchange(1, "EUR", "USD", date=datetime.date(2022, 1, 1)), Decimal("1.13")
        )

    def test_raises_exception_with_no_previous_data(self):
        with self.assertRaises(ExchangeRateUnavailable):
            exchange(1, "EUR", "USD", date=datetime.date(2021, 12, 30))

    def test_raises_exception_with_old_data(self):
        with self.settings(MAX_EXCHANGE_RATE_AGE=30):
            with self.assertRaises(ExchangeRateUnavailable):
                exchange(1, "EUR", "USD", date=datetime.date(2022, 2, 1))

    @mock.patch("historical_currencies.exchange.latest_rate")
    def test_without_date(self, latest_rate):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        latest_rate.return_value = (yesterday, Decimal(1))
        self.assertEqual(exchange(1, "EUR", "USD"), 1)
        latest_rate.assert_called_once_with("EUR", "USD", today)


class ComplexExchangeTestCase(TestCase):
    date_1 = datetime.date(2021, 12, 30)
    date_2 = datetime.date(2021, 12, 31)
    date_3 = datetime.date(2022, 1, 3)

    def setUp(self):
        latest_rate.cache_clear()
        _possible_base_currencies.cache_clear()
        ExchangeRate.objects.create(
            date=self.date_1, base_currency="USD", currency="EUR", rate=0.8823
        )
        ExchangeRate.objects.create(
            date=self.date_1, base_currency="USD", currency="ZAR", rate=15.897
        )
        ExchangeRate.objects.create(
            date=self.date_1, base_currency="EUR", currency="AUD", rate=1.5594
        )
        ExchangeRate.objects.create(
            date=self.date_2, base_currency="EUR", currency="USD", rate=1.1326
        )
        ExchangeRate.objects.create(
            date=self.date_2, base_currency="EUR", currency="ZAR", rate=18.0625
        )
        ExchangeRate.objects.create(
            date=self.date_3, base_currency="EUR", currency="USD", rate=1.1355
        )
        ExchangeRate.objects.create(
            date=self.date_3, base_currency="EUR", currency="ZAR", rate=17.966
        )

    def test_can_exchange_from_base(self):
        self.assertEqual(exchange(10, "USD", "EUR", date=self.date_1), Decimal("8.82"))
        self.assertEqual(exchange(10, "EUR", "USD", date=self.date_2), Decimal("11.33"))
        self.assertEqual(exchange(10, "EUR", "USD", date=self.date_3), Decimal("11.36"))

    def test_can_exchange_to_base(self):
        self.assertEqual(exchange(10, "EUR", "USD", date=self.date_1), Decimal("11.33"))
        self.assertEqual(exchange(10, "USD", "EUR", date=self.date_2), Decimal("8.83"))
        self.assertEqual(exchange(10, "USD", "EUR", date=self.date_3), Decimal("8.81"))

    def test_can_exchange_through_base(self):
        self.assertEqual(
            exchange(10, "EUR", "ZAR", date=self.date_1), Decimal("180.18")
        )
        self.assertEqual(
            exchange(10, "USD", "ZAR", date=self.date_2), Decimal("159.48")
        )
        self.assertEqual(
            exchange(10, "USD", "ZAR", date=self.date_3), Decimal("158.22")
        )
        self.assertEqual(exchange(100, "ZAR", "EUR", date=self.date_1), Decimal("5.55"))
        self.assertEqual(exchange(100, "ZAR", "USD", date=self.date_2), Decimal("6.27"))
        self.assertEqual(exchange(100, "ZAR", "USD", date=self.date_3), Decimal("6.32"))

    def test_cant_exchange_across_multiple_bases(self):
        with self.assertRaises(ExchangeRateUnavailable):
            exchange(1, "USD", "AUD", date=self.date_1)
        with self.assertRaises(ExchangeRateUnavailable):
            exchange(1, "ZAR", "AUD", date=self.date_1)


class CurrencyChoicesTestCase(SimpleTestCase):
    def test_expected_contents(self):
        choices = currency_choices()
        self.assertIn(("EUR", "EUR (Euro)"), choices)
        self.assertIn(("USD", "USD (US Dollar)"), choices)
        self.assertIn(("ZAR", "ZAR (Rand)"), choices)

    def test_skips_x_currencies(self):
        codes = [code for code, name in currency_choices()]
        self.assertNotIn("XTS", codes)
        self.assertNotIn("XXX", codes)
        self.assertIn("XCD", codes)

    def test_can_include_x_currencies(self):
        codes = [code for code, name in currency_choices(exclude_special=False)]
        self.assertIn("XTS", codes)
        self.assertIn("XXX", codes)
        self.assertIn("XCD", codes)


class CurrencyRenderTestCase(SimpleTestCase):
    def test_renders_rand(self):
        self.assertEqual(render_amount(Decimal(1000), "ZAR"), "1000.00 ZAR")

    def test_renders_yen(self):
        self.assertEqual(render_amount(Decimal(1000), "JPY"), "1000 JPY")


class TemplateTagTestCase(TestCase):
    def render_template(self, body, context, load_currency_format=True):
        if isinstance(context, dict):
            context = Context(context)
        if load_currency_format:
            body = "{% load currency_format %}" + body
        return Template(body).render(context)

    def test_currency_filter(self):
        rendered = self.render_template(
            "{{ ben|currency }}", {"ben": (Decimal(100), "USD")}
        )
        self.assertEqual(rendered, "100.00 USD")

    def test_exchange_filter_with_rate(self):
        date = datetime.date.today()
        ExchangeRate.objects.create(
            date=date, base_currency="EUR", currency="USD", rate=1.1326
        )
        rendered = self.render_template(
            "{{ eur|exchange:'USD' }}", {"eur": (Decimal(1), "EUR")}
        )
        self.assertEqual(rendered, "1.13 USD")

    def test_exchange_filter_missing_rate(self):
        with self.assertLogs(
            "historical_currencies.templatetags.currency_format",
            level="WARNING",
        ) as cm:
            rendered = self.render_template(
                "{{ eur|exchange:'USD' }}", {"eur": (Decimal(1), "EUR")}
            )
        self.assertEqual(rendered, "? (no rate) USD")
        self.assertEqual(len(cm.records), 1)
        log = cm.records[0]
        self.assertEqual(log.message, "Missing Exchange Rate: EUR:USD")


class CurrencyFreshnessCheckTestCase(TestCase):
    def test_fails_when_exchange_data_is_stale(self):
        errors = check_fresh_exchange_rate_data(None)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.level, 40)
        self.assertEqual(error.msg, "no current exchange rates")

    def test_passes_when_exchange_data_is_fresh(self):
        date = datetime.date.today()
        ExchangeRate.objects.create(
            date=date, base_currency="EUR", currency="USD", rate=1.1326
        )
        errors = check_fresh_exchange_rate_data(None)
        self.assertEqual(errors, [])


@tag("internet")
class ManagementCommandTestCase(TestCase):
    def test_ecb_daily_import(self):
        last_week = datetime.date.today() - datetime.timedelta(days=7)
        rates = ExchangeRate.objects.filter(
            currency="USD", base_currency="EUR", date__gte=last_week
        )
        self.assertFalse(rates.exists())
        out = StringIO()
        call_command("import_ecb_exchangerates", "--daily", stdout=out)
        self.assertTrue(rates.exists())
