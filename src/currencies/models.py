from datetime import date, timedelta

from django.conf import settings
from django.core.checks import Error, Tags, register
from django.db import models


class ExchangeRate(models.Model):
    date = models.DateField()
    currency = models.CharField(max_length=3)
    base_currency = models.CharField(max_length=3)
    rate = models.DecimalField(decimal_places=5, max_digits=15)

    class Meta:
        unique_together = [
            ["date", "currency", "base_currency"],
        ]

    def __str__(self):
        return f"Exchange Rate: {self.base_currency}-{self.currency} @ {self.date}: {self.rate}"


@register(Tags.database, deploy=True)
def check_fresh_exchange_rate_data(app_configs, **kwargs):
    errors = []
    oldest_acceptable_rate = date.today() - timedelta(
        days=settings.MAX_EXCHANGE_RATE_AGE
    )
    rates = ExchangeRate.objects.filter(date__gte=oldest_acceptable_rate)
    if not rates.exists():
        errors.append(
            Error(
                "no current exchange rates",
                hint="Run manage.py import_ecb_exchangerates to populate exchange rates",
                id="currencies.E001",
            )
        )

    return errors
