from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Accommodation

class AccommodationSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating accommodation information"""
    address = serializers.CharField(write_only=True)
    formatted_address = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'type', 'price', 'beds', 'bedrooms', 
                 'available_from', 'available_to', 'address', 'formatted_address',
                 'reserved', 'userID', 'building_name', 'region', 
                 'contact_phone', 'contact_email']
        read_only_fields = ['id', 'latitude', 'longitude', 'building_name', 
                           'estate_name', 'street_name', 'building_no', 'district', 
                           'region', 'formatted_address']
    
    @extend_schema_field(serializers.CharField())
    def get_formatted_address(self, obj) -> str:
        return obj.formatted_address()

class AccommodationDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying accommodation details"""
    formatted_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'type', 'price', 'beds', 'bedrooms', 
                 'available_from', 'available_to', 'region', 'reserved', 'formatted_address',
                 'building_name', 'userID', 'contact_phone', 'contact_email']
    
    @extend_schema_field(serializers.CharField())
    def get_formatted_address(self, obj) -> str:
        return obj.formatted_address()

class AccommodationListSerializer(serializers.ModelSerializer):
    """Serializer for listing accommodations"""
    distance = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'building_name', 'description', 'type', 'price', 'beds', 'bedrooms',
                 'available_from', 'available_to', 'region', 'distance', 'reserved', 'contact_phone', 'contact_email']
