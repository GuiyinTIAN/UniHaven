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

    # 新增唯一识别字段
    room_number = models.CharField(max_length=20, blank=True, null=True)
    floor_number = models.CharField(max_length=20, blank=True, null=True)
    flat_number  = models.CharField(max_length=20, blank=True, null=True)

    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    rating_sum = models.FloatField(default=0.0)  
    rating_count = models.IntegerField(default=0)

    # 添加关联大学的多对多关系
    affiliated_universities = models.ManyToManyField(
        'University', 
        through='AccommodationUniversity',
        related_name='listed_accommodations',
        blank=True,
        help_text="提供该住宿的大学"
    )

    def save(self, *args, **kwargs):
        # 确保空值被转换为空字符串，以避免NULL值导致的唯一约束问题
        self.room_number = self.room_number or ""
        self.floor_number = self.floor_number or ""
        self.flat_number = self.flat_number or ""
        self.geo_address = self.geo_address or ""
        super().save(*args, **kwargs)

    def formatted_address(self):
        parts = [
            self.building_name,
            self.estate_name,
            f"{self.building_no} {self.street_name}".strip(),
            self.district,
            self.region
        ]
        return ", ".join(filter(None, parts))

    class Meta:
        unique_together = (
            'room_number',
            'flat_number',
            'floor_number',
            'geo_address',
        )

class AccommodationRating(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='ratings')
    user_identifier = models.CharField(max_length=200)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['accommodation', 'user_identifier']  # Prevent duplicate ratings

    def __str__(self):
        return f"{self.user_identifier} rated {self.accommodation.title} ({self.rating})"

class University(models.Model):
    """Model to store university information"""
    code = models.CharField(max_length=10, unique=True, help_text="大学代码，如HKU, HKUST")
    name = models.CharField(max_length=100, help_text="大学全名")
    specialist_email = models.EmailField(help_text="该大学住宿专家的邮箱")
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        verbose_name_plural = "Universities"

class AccommodationUniversity(models.Model):
    """Many-to-many relationship between Accommodation and University"""
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='universities')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='accommodations')
    date_added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('accommodation', 'university')
        verbose_name_plural = "Accommodation Universities"
    
    def __str__(self):
        return f"{self.accommodation.title} - {self.university.code}"

class UniversityAPIKey(models.Model):
    """管理大学系统的API密钥"""
    university = models.OneToOneField(University, on_delete=models.CASCADE, related_name='api_key')
    key = models.CharField(max_length=64, unique=True, help_text="API密钥，用于认证请求")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.university.name} API Key"
    
    def save(self, *args, **kwargs):
        # 如果没有指定key，生成一个随机的UUID作为key
        if not self.key:
            import uuid
            self.key = str(uuid.uuid4()).replace('-', '')
        super().save(*args, **kwargs)



