from django.contrib import admin

from currencies.models import ExchangeRate


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("date", "currency", "base_currency", "rate")
    date_hierarchy = "date"
