from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Accommodation, AccommodationRating, ReservationPeriod

class AddAccommodationSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating new accommodation"""
    building_name = serializers.CharField(
        help_text="Full address to be looked up via government API"
    )
    room_number = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        help_text="Room number (may be null if the property is an entire flat)"
    )
    floor_number = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        help_text="Floor number of the building"
    )
    flat_number = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        help_text="Flat/unit number on the floor"
    )
    
    class Meta:
        model = Accommodation
        fields = [
            'title', 'description', 'type', 'price', 'beds', 'bedrooms',
            'available_from', 'available_to', 'building_name',
            'room_number', 'floor_number', 'flat_number', 'contact_name',
            'contact_phone', 'contact_email'
        ]

    def validate(self, data):
        """
        Check that the accommodation with same unique identifier doesn't already exist
        """
        # If a GeoAddress is provided, check whether the same accommodation already exists
        if 'geo_address' in self.initial_data:
            geo_address = self.initial_data['geo_address']
            flat_number = data.get('flat_number') 
            floor_number = data.get('floor_number')
            room_number = data.get('room_number')
            
            if Accommodation.objects.filter(
                geo_address=geo_address,
                flat_number=flat_number,
                floor_number=floor_number,
                room_number=room_number
            ).exists():
                raise serializers.ValidationError(
                    "This accommodation already exists with the same room, flat, floor and address."
                )
        
        return data

class AccommodationSerializer(serializers.ModelSerializer):
    """General serializer for accommodation information"""
    address = serializers.CharField(write_only=True)
    formatted_address = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'type', 'price', 'beds', 'bedrooms', 
                 'available_from', 'available_to', 'address', 'formatted_address',
                 'reserved', 'userID', 'building_name', 'region', 
                 'room_number', 'floor_number', 'flat_number', 'contact_name',
                 'contact_phone', 'contact_email','rating', 'rating_count']
        read_only_fields = ['id', 'latitude', 'longitude', 'building_name', 
                           'estate_name', 'street_name', 'building_no', 'district', 
                           'region', 'formatted_address']
    
    @extend_schema_field(serializers.CharField())
    def get_formatted_address(self, obj) -> str:
        return obj.formatted_address()

    def to_representation(self, instance):
        """Add the complete address information of the accommodation"""
        representation = super().to_representation(instance)
        representation['address_details'] = {
            'room_number': instance.room_number,
            'flat_number': instance.flat_number,
            'floor_number': instance.floor_number,
            'formatted_address': instance.formatted_address()
        }
        return representation

class ReservationPeriodSerializer(serializers.ModelSerializer):
    """序列化器用于预定时间段"""
    class Meta:
        model = ReservationPeriod
        fields = ['id', 'user_id', 'contact_number', 'start_date', 'end_date', 'created_at']

class AccommodationDetailSerializer(serializers.ModelSerializer):
    """Serializer for accommodation detail view"""
    formatted_address = serializers.CharField(read_only=True)
    university_codes = serializers.SerializerMethodField()
    reservation_periods = ReservationPeriodSerializer(many=True, read_only=True)
    available_periods = serializers.SerializerMethodField()
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'type', 'beds', 'bedrooms',
                  'price', 'available_from', 'available_to', 'latitude', 'longitude',
                  'formatted_address', 'rating', 'reserved', 'userID',
                  'reservation_contact_number', 'region', 'university_codes',
                  'reservation_periods', 'available_periods']
                  
    def get_university_codes(self, obj):
        return [univ.code for univ in obj.affiliated_universities.all()]
        
    def get_available_periods(self, obj):
        """获取可用时间段"""
        periods = obj.get_available_periods()
        return [{'start_date': start_date, 'end_date': end_date} for start_date, end_date in periods]

class AccommodationListSerializer(serializers.ModelSerializer):
    """Serializer for listing accommodations"""
    distance = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'building_name', 'description', 'type', 'price', 'beds', 'bedrooms',
                 'available_from', 'available_to', 'region', 'distance', 'reserved', 
                 'room_number', 'floor_number', 'flat_number', 'contact_name',
                 'contact_phone', 'contact_email','rating', 'rating_count', 'rating_sum',
                 'userID', 'reservation_contact_number']  
        
class RatingSerializer(serializers.Serializer):
    """Serializer for validating accommodation rating input"""
    rating = serializers.IntegerField(min_value=0, max_value=5)
