from rest_framework import serializers
from .serializers import AccommodationDetailSerializer

class MessageResponseSerializer(serializers.Serializer):
    """Serializer for simple message responses"""
    message = serializers.CharField()

class AddressResponseSerializer(serializers.Serializer):
    """Serializer for address lookup responses"""
    EnglishAddress = serializers.DictField()
    ChineseAddress = serializers.DictField()
    GeospatialInformation = serializers.DictField()

class SuccessResponseSerializer(serializers.Serializer):
    """Serializer for success responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses"""
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.DictField(required=False)

class ReservationResponseSerializer(serializers.Serializer):
    """Serializer for reservation and cancellation responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    UserID = serializers.CharField(required=False)
    accommodation = AccommodationDetailSerializer(required=False)

class AccommodationListResponseSerializer(serializers.Serializer):
    """Serializer for accommodation list responses"""
    accommodations = serializers.ListField(
        child=serializers.DictField()
    )

class DeleteAccommodationRequestSerializer(serializers.Serializer):
    """Serializer for delete accommodation request"""
    id = serializers.IntegerField(required=True)

class DuplicateAccommodationResponseSerializer(serializers.Serializer):
    """Serializer for duplicate accommodation check responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    duplicates = serializers.ListField(child=serializers.DictField(), required=False)
    already_associated = serializers.BooleanField(required=False)
    accommodation_id = serializers.IntegerField(required=False)
    accommodation_title = serializers.CharField(required=False)

class TemplateResponseSerializer(serializers.Serializer):
    """Empty serializer for views that return template responses"""
    pass

class ApiKeyTestResponseSerializer(serializers.Serializer):
    """Serializer for API key test responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    university = serializers.CharField()
    code = serializers.CharField()

class LinkAccommodationResponseSerializer(serializers.Serializer):
    """Serializer for accommodation linking responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    id = serializers.IntegerField(required=False)

class ReservationViewResponseSerializer(serializers.Serializer):
    """Serializer for reservation view responses"""
    reservations = serializers.ListField(required=False)
    user_id = serializers.CharField(required=False)
    error = serializers.CharField(required=False)