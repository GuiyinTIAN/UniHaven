# Generated by Django 5.1.7 on 2025-03-30 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accommodation", "0003_accommodation_userid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accommodation",
            name="userID",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
