from django.db import migrations, models
import django.db.models.deletion

def create_initial_universities(apps, schema_editor):
    University = apps.get_model('accommodation', 'University')
    
    universities = [
        {'code': 'HKU', 'name': 'The University of Hong Kong', 'specialist_email': 'cedars@hku.hk'},
        {'code': 'HKUST', 'name': 'Hong Kong University of Science and Technology', 'specialist_email': 'housing@ust.hk'},
        {'code': 'CUHK', 'name': 'The Chinese University of Hong Kong', 'specialist_email': 'housing@cuhk.edu.hk'},
    ]
    
    for university_data in universities:
        University.objects.create(**university_data)

class Migration(migrations.Migration):

    dependencies = [
        ('accommodation', '0002_add_unique_address_fields'),  # 确保依赖上一个迁移
    ]

    operations = [
        migrations.CreateModel(
            name='University',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='大学代码，如HKU, HKUST', max_length=10, unique=True)),
                ('name', models.CharField(help_text='大学全名', max_length=100)),
                ('specialist_email', models.EmailField(help_text='该大学住宿专家的邮箱', max_length=254)),
            ],
            options={
                'verbose_name_plural': 'Universities',
            },
        ),
        migrations.CreateModel(
            name='AccommodationUniversity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('accommodation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='universities', to='accommodation.accommodation')),
                ('university', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accommodations', to='accommodation.university')),
            ],
            options={
                'verbose_name_plural': 'Accommodation Universities',
                'unique_together': {('accommodation', 'university')},
            },
        ),
        migrations.AddField(
            model_name='accommodation',
            name='affiliated_universities',
            field=models.ManyToManyField(blank=True, help_text='提供该住宿的大学', related_name='listed_accommodations', through='accommodation.AccommodationUniversity', to='accommodation.university'),
        ),
        migrations.RunPython(create_initial_universities),
    ]
