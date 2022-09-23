from decimal import Decimal
import datetime

from django.test import TestCase

from currencies.exchange import exchange
from currencies.models import ExchangeRate


class ExchangeTestCase(TestCase):
    date = datetime.date(2021, 12, 31)

    def setUp(self):
        ExchangeRate.objects.create(
            date=self.date, base_currency="EUR", currency="USD", rate=1.1326
        )
        ExchangeRate.objects.create(
            date=self.date, base_currency="EUR", currency="ZAR", rate=18.0625
        )

    def test_can_echange_from_base(self):
        self.assertEqual(exchange(1, "EUR", "USD", date=self.date), Decimal("1.13"))

    def test_can_echange_to_base(self):
        self.assertEqual(exchange(1, "USD", "EUR", date=self.date), Decimal("0.88"))

    def test_can_echange_through_base(self):
        self.assertEqual(exchange(1, "USD", "ZAR", date=self.date), Decimal("15.95"))

    def test_uses_last_valid_rate(self):
        self.assertEqual(
            exchange(1, "EUR", "USD", date=datetime.date(2022, 1, 1)), Decimal("1.13")
        )
