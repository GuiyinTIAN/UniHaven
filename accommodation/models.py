from django.db import models


class Accommodation(models.Model):
    TYPE_CHOICES = [
        ('APARTMENT', 'Apartment'),
        ('HOUSE', 'House'),
        ('HOSTEL', 'Hostel'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    beds = models.IntegerField()
    bedrooms = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    latitude = models.FloatField()
    longitude = models.FloatField()
    geo_address = models.CharField(max_length=200)
    rating = models.FloatField(default=0.0)  # Average rating (0-5 scale)
    region = models.CharField(max_length=100, default="")  # 新增字段存储地区信息


