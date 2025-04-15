from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    # userID is the ID for resevation and cancellation
    userID = models.CharField(max_length=255, blank=True, default="")
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
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    rating_sum = models.FloatField(default=0.0)  
    rating_count = models.IntegerField(default=0)

    def formatted_address(self):
        parts = [
            self.building_name,
            self.estate_name,
            f"{self.building_no} {self.street_name}".strip(),
            self.district,
            self.region
        ]
        return ", ".join(filter(None, parts))

class AccommodationRating(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='ratings')
    user_identifier = models.CharField(max_length=200)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['accommodation', 'user_identifier']  # Prevent duplicate ratings

    def __str__(self):
        return f"{self.user_identifier} rated {self.accommodation.title} ({self.rating})"


