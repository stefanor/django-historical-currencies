# Generated by Django 4.1.1 on 2022-09-23 12:23

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExchangeRate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                ("currency", models.CharField(max_length=3)),
                ("base_currency", models.CharField(max_length=3)),
                ("rate", models.DecimalField(decimal_places=5, max_digits=15)),
            ],
            options={
                "unique_together": {("date", "currency", "base_currency")},
            },
        ),
    ]
