from decimal import Decimal

from django.test import SimpleTestCase

from historical_currencies.formatting import render_amount


class CurrencyRenderTestCase(SimpleTestCase):
    def test_renders_rand(self):
        self.assertEqual(render_amount(Decimal(1000), "ZAR"), "1000.00 ZAR")

    def test_renders_yen(self):
        self.assertEqual(render_amount(Decimal(1000), "JPY"), "1000 JPY")
