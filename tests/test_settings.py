from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

SECRET_KEY = "fake-key"

INSTALLED_APPS = [
    "historical_currencies",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": TESTS_DIR / "db.sqlite3",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
    },
]

MAX_EXCHANGE_RATE_AGE = 30
