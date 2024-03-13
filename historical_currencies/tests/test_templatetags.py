import datetime
from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase, TestCase

from iso4217 import Currency

from historical_currencies.models import ExchangeRate


class CurrencyTagTestCase(SimpleTestCase):
    def render(self, body, context):
        if isinstance(context, dict):
            context = Context(context)
        body = "{% load currency_format %}" + body
        return Template(body).render(context)

    def test_currency_filter(self):
        rendered = self.render("{{ ben|currency }}", {"ben": (Decimal(100), "USD")})
        self.assertEqual(rendered, "100.00 USD")


class ExchangeRateTagTestCase(TestCase):
    def render(self, body, context):
        if isinstance(context, dict):
            context = Context(context)
        body = "{% load currency_format %}" + body
        return Template(body).render(context)

    def test_exchange_filter_with_rate(self):
        date = datetime.date.today()
        ExchangeRate.objects.create(
            date=date, base_currency="EUR", currency="USD", rate=1.1326
        )
        rendered = self.render("{{ eur|exchange:'USD' }}", {"eur": (Decimal(1), "EUR")})
        self.assertEqual(rendered, "1.13 USD")

    def test_exchange_filter_missing_rate(self):
        with self.assertLogs(
            "historical_currencies.templatetags.currency_format",
            level="WARNING",
        ) as cm:
            rendered = self.render(
                "{{ eur|exchange:'USD' }}", {"eur": (Decimal(1), "EUR")}
            )
        self.assertEqual(rendered, "? (no rate) USD")
        self.assertEqual(len(cm.records), 1)
        log = cm.records[0]
        self.assertEqual(log.message, "Missing Exchange Rate: EUR:USD")


class CurrencyChoicesListTagTestCase(SimpleTestCase):
    def render(self, body, context):
        if isinstance(context, dict):
            context = Context(context)
        body = "{% load currency_choices %}" + body
        return Template(body).render(context)

    def test_currency_choices_list(self):
        rendered = self.render(
            "{% currency_choices_list as choices %}"
            "{% for code, name in choices %}"
            "[{{ code }}] {{ name }}\n"
            "{% endfor %}",
            {},
        )
        lines = rendered.splitlines()
        self.assertTrue(len(lines) > 10)
        self.assertIn(f"[USD] USD ({Currency('USD').currency_name})", lines)


class CurrencyChoicesOptionsTagTestCase(SimpleTestCase):
    def render(self, body, context):
        if isinstance(context, dict):
            context = Context(context)
        body = "{% load currency_choices %}" + body
        return Template(body).render(context)

    def test_currency_choices_options(self):
        rendered = self.render("{% currency_choices_options %}\n", {})
        self.assertInHTML(
            f'<option value="USD">USD ({Currency("USD").currency_name})</option>',
            rendered,
        )

    def test_currency_choices_options_selected(self):
        rendered = self.render("{% currency_choices_options selected='USD' %}\n", {})
        self.assertInHTML(
            f'<option value="USD" selected>USD ({Currency("USD").currency_name})</option>',
            rendered,
        )
