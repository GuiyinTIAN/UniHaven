# Generated by Django 5.1.7 on 2025-04-25 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accommodation", "0007_merge_20250425_1343"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accommodation",
            name="flat_number",
            field=models.CharField(
                blank=True, help_text="单元号", max_length=20, null=True
            ),
        ),
        migrations.AlterField(
            model_name="accommodation",
            name="floor_number",
            field=models.CharField(
                blank=True, help_text="楼层号", max_length=20, null=True
            ),
        ),
    ]
