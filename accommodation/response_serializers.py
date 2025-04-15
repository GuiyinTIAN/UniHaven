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
