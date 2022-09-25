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
