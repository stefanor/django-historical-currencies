import logging

from django import template
from django.utils.translation import gettext_lazy as _

from historical_currencies.exceptions import ExchangeRateUnavailable
from historical_currencies.exchange import exchange
from historical_currencies.formatting import render_amount

register = template.Library()
log = logging.getLogger(__name__)


@register.filter
def currency(amount):
    """Format a tuple (amount, currency)"""
    amount, currency = amount
    return render_amount(amount, currency)


@register.filter(name="exchange")
def exchange_filter(amount, target_currency):
    """Exchange a tuple (amount, currency) to target_currency and format it"""
    amount, source_currency = amount
    try:
        amount = exchange(amount, source_currency, target_currency)
    except ExchangeRateUnavailable:
        log.warning("Missing Exchange Rate: %s:%s", source_currency, target_currency)
        return _("? (no rate) %(target_currency)s") % {
            "target_currency": target_currency
        }
    return render_amount(amount, target_currency)
