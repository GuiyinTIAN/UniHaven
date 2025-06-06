# Generated by Django 5.1.7 on 2025-04-29 08:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accommodation", "0011_accommodation_contact_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="accommodation",
            name="contract_status",
            field=models.BooleanField(
                default=False, help_text="Whether the accommodation is singed contract"
            ),
        ),
    ]
