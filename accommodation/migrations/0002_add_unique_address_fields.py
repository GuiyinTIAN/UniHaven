from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accommodation', '0001_initial'),  # 替换为您的上一个迁移
    ]

    operations = [
        migrations.AddField(
            model_name='accommodation',
            name='room_number',
            field=models.CharField(blank=True, help_text='房号，可为空', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='accommodation',
            name='floor_number',
            field=models.CharField(default='1', help_text='楼层号', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='accommodation',
            name='flat_number',
            field=models.CharField(default='A', help_text='单元号', max_length=20),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='accommodation',
            unique_together={('room_number', 'flat_number', 'floor_number', 'geo_address')},
        ),
    ]
