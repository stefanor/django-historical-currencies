# Django currencies with historical exchange rates

This is a fairly minimal Django app that renders amounts of currencies,
stores historical exchange rates in the database, and performs currency
conversion.

When working with any historical multi-currency data, one often needs to
be able to perform exchange rate calculations with historical rates.
This allows the conversion to be accurately reproduced in the future.

Exchange Rates are stored in a simple database table, with 1 row per
rate per date.
Conversions can be done directly, or across a base currency using 2
rates.

Formatting is defined by [`iso4217`](https://pypi.org/project/iso4217/).
Exchange Rate data can be sourced from:

* The [European ECB Reference Rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
* [openexchangerates.org](https://openexchangerates.org/) (requires free
  registration)

## Installation

1. Install `django-historical-currencies` in your Python environment.
1. Add `historical_currencies` to `INSTALLED_APPS` in your
   `settings.py`.
1. Import yesterday's exchange rates to get started:
   `manage.py import_ecb_exchangerates --daily`.
1. Configure a periodic task (e.g. cron, systemd timer, celery beat) to
   import daily exchange rates.

## Settings

* `MAX_EXCHANGE_RATE_AGE`: How many days old can an exchange rate be
  treated as current?

Optional settings, only required for OpenExchangeRates.org import:

* `OPEN_EXCHANGE_RATES_APP_ID`: OpenExchangeRates App ID.
* `OPEN_EXCHANGE_RATES_BASE_CURRENCY`: Base currency.

## License

This Django app is available under the terms of the ISC license, see
`LICENSE`.
