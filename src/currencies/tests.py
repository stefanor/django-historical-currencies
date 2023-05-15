import datetime
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase, TestCase

import currencies.exchange  # imported for mock patching # noqa: F401
from currencies.choices import currency_choices
from currencies.exceptions import ExchangeRateUnavailable
from currencies.exchange import exchange, latest_rate, _possible_base_currencies
from currencies.formatting import render_amount
from currencies.models import ExchangeRate


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

    @mock.patch("currencies.exchange.latest_rate")
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


class CurrencyRenderTestCase(TestCase):
    def test_renders_rand(self):
        self.assertEqual(render_amount(Decimal(1000), "ZAR"), "1000.00 ZAR")

    def test_renders_yen(self):
        self.assertEqual(render_amount(Decimal(1000), "JPY"), "1000 JPY")
