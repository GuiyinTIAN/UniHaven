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
    available_from = models.DateField(null=True, blank=True)
    available_to = models.DateField(null=True, blank=True)

    # 添加联系方式字段
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    userID = models.CharField(max_length=255, blank=True, default="")
    #If reserved is true, the accommodation is reserved
    reserved = models.BooleanField(default=False)

    building_name = models.CharField(max_length=200, default="", blank=True)
    estate_name = models.CharField(max_length=200, default="", blank=True)
    street_name = models.CharField(max_length=200, default="", blank=True)
    building_no = models.CharField(max_length=20, default="", blank=True)
    district = models.CharField(max_length=200, default="", blank=True)
    region = models.CharField(max_length=100, default="", blank=True)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    geo_address = models.CharField(max_length=200, blank=True)

    rating = models.FloatField(default=0.0, blank=True)

    def formatted_address(self):
        parts = [
            self.building_name,
            self.estate_name,
            f"{self.building_no} {self.street_name}".strip(),
            self.district,
            self.region
        ]
        return ", ".join(filter(None, parts))


