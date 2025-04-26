from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Accommodation

class AddAccommodationSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating new accommodation"""
    address = serializers.CharField(
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
            'available_from', 'available_to', 'address',
            'room_number', 'floor_number', 'flat_number',
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
                 'room_number', 'floor_number', 'flat_number',
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

class AccommodationDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying accommodation details"""
    formatted_address = serializers.SerializerMethodField()
    affiliated_university_codes = serializers.SerializerMethodField()
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'type', 'price', 'beds', 'bedrooms', 
                 'available_from', 'available_to', 'region', 'reserved', 'formatted_address',
                 'building_name', 'userID', 'room_number', 'floor_number', 'flat_number',
                 'contact_phone', 'contact_email', 'rating', 'rating_count', 'rating_sum',
                 'affiliated_university_codes']
    
    @extend_schema_field(serializers.CharField())
    def get_formatted_address(self, obj) -> str:
        return obj.formatted_address()
        
    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_affiliated_university_codes(self, obj):
        """Get the code list of the associated university"""
        return [univ.code for univ in obj.affiliated_universities.all()]

class AccommodationListSerializer(serializers.ModelSerializer):
    """Serializer for listing accommodations"""
    distance = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'building_name', 'description', 'type', 'price', 'beds', 'bedrooms',
                 'available_from', 'available_to', 'region', 'distance', 'reserved', 
                 'room_number', 'floor_number', 'flat_number',
                 'contact_phone', 'contact_email','rating', 'rating_count', 'rating_sum']
        
class RatingSerializer(serializers.Serializer):
    """Serializer for validating accommodation rating input"""
    rating = serializers.IntegerField(min_value=0, max_value=5)
