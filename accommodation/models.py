from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta

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

    # Accommodation Owner Information
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    # 移除过时字段
    # contract_status 字段已移除，合同状态将记录在ReservationPeriod中

    building_name = models.CharField(max_length=200, default="", blank=True)
    estate_name = models.CharField(max_length=200, default="", blank=True)
    street_name = models.CharField(max_length=200, default="", blank=True)
    building_no = models.CharField(max_length=20, default="", blank=True)
    district = models.CharField(max_length=200, default="", blank=True)
    region = models.CharField(max_length=100, default="", blank=True)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    geo_address = models.CharField(max_length=200, blank=True)

    room_number = models.CharField(max_length=20, blank=True, null=True)
    floor_number = models.CharField(max_length=20, blank=True, null=True)
    flat_number  = models.CharField(max_length=20, blank=True, null=True)

    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    rating_sum = models.FloatField(default=0.0)  
    rating_count = models.IntegerField(default=0)

    affiliated_universities = models.ManyToManyField(
        'University', 
        through='AccommodationUniversity',
        related_name='listed_accommodations',
        blank=True,
        help_text="The university that provides this accommodation"
    )

    def save(self, *args, **kwargs):
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

    def is_available(self, start_date, end_date):
        """
        检查在给定的时间段内是否可预定
        """
        # 检查是否在住宿的可用时间范围内
        if start_date < self.available_from or end_date > self.available_to:
            return False
            
        # 检查是否与现有预定时间段重叠
        overlapping_reservations = self.reservation_periods.filter(
            models.Q(start_date__lte=end_date) & models.Q(end_date__gte=start_date)
        ).exists()
        
        return not overlapping_reservations

    def get_available_periods(self):
        """
        获取所有可用的时间段，返回一个时间段列表
        只返回长度不少于MIN_BOOKING_DAYS天的时间段
        """
        if not self.available_from or not self.available_to:
            return []
            
        # 设置最小可预订时间（天）
        MIN_BOOKING_DAYS = 2
        
        # 获取所有预定期间，按开始日期排序
        reserved_periods = list(self.reservation_periods.all().order_by('start_date'))
        
        # 如果没有预定，则整个时间段都可用
        if not reserved_periods:
            return [(self.available_from, self.available_to)]
            
        available_periods = []
        current_date = self.available_from
        
        # 遍历所有预定期间，找出中间的可用时间段
        for period in reserved_periods:
            # 如果当前日期小于预定开始日期，则添加可用时间段
            # 修复：使用预定开始日期减去1天作为可用时间段的结束日期
            if current_date < period.start_date:
                end_date = period.start_date - timedelta(days=1)
                # 检查这个时间段是否至少有MIN_BOOKING_DAYS天
                days_available = (end_date - current_date).days + 1
                if days_available >= MIN_BOOKING_DAYS:
                    available_periods.append((current_date, end_date))
            # 更新当前日期为预定结束日期加1天
            current_date = period.end_date + timedelta(days=1)
            
        # 检查最后一个预定结束日期到可用结束日期是否还有空闲时间段
        if current_date <= self.available_to:
            days_available = (self.available_to - current_date).days + 1
            if days_available >= MIN_BOOKING_DAYS:
                available_periods.append((current_date, self.available_to))
            
        return available_periods

    def is_reserved(self):
        """Check if the accommodation has been fully booked (there are no available time slots)"""
        return len(self.get_available_periods()) == 0

    class Meta:
        unique_together = (
            'room_number',
            'flat_number',
            'floor_number',
            'geo_address',
        )

class ReservationPeriod(models.Model):
    """Model to store Users' reservation periods for accommodations"""
    accommodation = models.ForeignKey(
        Accommodation, 
        on_delete=models.CASCADE, 
        related_name='reservation_periods'
    )
    user_id = models.CharField(max_length=255, help_text="Student's ID")
    contact_number = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField(help_text="Reservation start date")
    end_date = models.DateField(help_text="Reservation end date")
    created_at = models.DateTimeField(auto_now_add=True)
    # 添加合同状态字段到预订记录
    contract_status = models.BooleanField(default=False, help_text="Whether this reservation has a signed contract")
    
    def __str__(self):
        return f"{self.accommodation.title} - {self.start_date} to {self.end_date} by {self.user_id}"
    
    class Meta:
        ordering = ['start_date']

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
    code = models.CharField(max_length=10, unique=True, help_text="University codes, such as HKU, HKUST and CUHK etc.")
    name = models.CharField(max_length=100, help_text="Full name of the university")
    specialist_email = models.EmailField(help_text="The email address of the accommodation expert of this university")
    
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
    """Manage the API keys of the university system"""
    university = models.OneToOneField(University, on_delete=models.CASCADE, related_name='api_key')
    key = models.CharField(max_length=64, unique=True, help_text="API key, used for authentication requests")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.university.name} API Key"
    
    def save(self, *args, **kwargs):
        if not self.key:
            import uuid
            self.key = str(uuid.uuid4()).replace('-', '')
        super().save(*args, **kwargs)



