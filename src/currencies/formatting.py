from decimal import Decimal

from iso4217 import Currency


def render_amount(amount, currency_code):
    currency = Currency(currency_code)
    quantization = Decimal(10) ** -currency.exponent
    quantized = amount.quantize(quantization)
    return f"{quantized} {currency.code}"
