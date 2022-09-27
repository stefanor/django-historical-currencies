from django import template

from currencies.exchange import exchange
from currencies.formatting import render_amount

register = template.Library()


@register.filter
def currency(amount):
    """Format a tuple (amount, currency)"""
    amount, currency = amount
    return render_amount(amount, currency)


@register.filter(name="exchange")
def exchange_filter(amount, target_currency):
    """Exchange a tuple (amount, currency) to target_currency and format it"""
    amount, source_currency = amount
    amount = exchange(amount, source_currency, target_currency)
    return render_amount(amount, target_currency)
