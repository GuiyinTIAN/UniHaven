"""
Views for the accommodation application.

This module contains all the view functions and classes for the UniHaven accommodation system,
organized by functional areas:
- Home/index
- Address lookup
- Accommodation management (add, list, search, view)
- Reservation operations (reserve, cancel)
"""
import requests
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.utils.dateparse import parse_date
from django.db.models import Q, F, Func, FloatField, ExpressionWrapper, Exists, OuterRef
from django.urls import reverse
from django.core.mail import send_mail

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, renderer_classes, authentication_classes, permission_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .models import Accommodation, AccommodationRating, UniversityAPIKey, ReservationPeriod
from .forms import AccommodationForm
from .serializers import (
    AccommodationSerializer, 
    AccommodationDetailSerializer,
    AccommodationListSerializer,
    RatingSerializer,
    AddAccommodationSerializer
)
from .response_serializers import (
    MessageResponseSerializer,
    AddressResponseSerializer,
    SuccessResponseSerializer,
    ErrorResponseSerializer,
    ReservationResponseSerializer,
    AccommodationListResponseSerializer,
    DeleteAccommodationRequestSerializer,
    DuplicateAccommodationResponseSerializer,
    TemplateResponseSerializer,
    LinkAccommodationResponseSerializer,
    ApiKeyTestResponseSerializer
)
from .utils import get_university_from_user_id
from .authentication import UniversityAPIKeyAuthentication
from .permissions import UniversityAccessPermission

#------------------------------------------------------------------------------
# Constants and Configurations
CAMPUS_LOCATIONS = {
    "HKU_main": {"latitude": 22.28405, "longitude": 114.13784},
    "HKU_sassoon": {"latitude": 22.2675, "longitude": 114.12881},
    "HKU_swire": {"latitude": 22.20805, "longitude": 114.26021},
    "KHU_kadoorie": {"latitude": 22.43022, "longitude": 114.11429},
    "HKU_dentistry": {"latitude": 22.28649, "longitude": 114.14426},
    # other campuses can be added here
    "HKUST": {"latitude": 22.33584, "longitude": 114.26355},
    "HKUST": {"latitude": 22.41907, "longitude": 114.20693},
}

# API Key Parameters for Swagger UI
API_KEY_PARAMETER = [
    OpenApiParameter(
        name="X-API-Key", 
        location=OpenApiParameter.HEADER, 
        description="API key, used to identify requests from university systems", 
        type=str, 
        required=False
    ),
    OpenApiParameter(
        name="api_key", 
        location=OpenApiParameter.QUERY, 
        description="API key (if the request header method is not used), used to identify the requests of the university system", 
        type=str, 
        required=False
    )
]

#------------------------------------------------------------------------------
# Home Page
#------------------------------------------------------------------------------
@extend_schema(
    summary="Home Page",
    description="Home page view function",
    responses={200: MessageResponseSerializer}
)
@api_view(['GET'])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def index(request):
    """
    Home page view function.

    Returns:
        - HTML template if no specific format is requested
        - JSON welcome message if JSON format is requested
    """
    if request.accepted_renderer.format == 'json':
        return Response({"message": "Welcome to UniHaven!"})
    return Response({}, template_name='accommodation/index.html')

#------------------------------------------------------------------------------
# Address Lookup
#------------------------------------------------------------------------------
@extend_schema(
    summary="Address Lookup",
    description="Call Hong Kong government API to look up addresses",
    parameters=[
        OpenApiParameter(name="address", location=OpenApiParameter.QUERY, required=True, type=str)
    ],
    responses={
        200: AddressResponseSerializer,
        400: OpenApiResponse(description="Address parameter is required"),
        404: OpenApiResponse(description="No results found"),
        500: OpenApiResponse(description="API error")
    }
)
@api_view(['GET'])
def lookup_address(request):
    """
    Call Hong Kong government API to look up addresses.

    Uses the Address Lookup Service (ALS) from the Hong Kong government to
    retrieve detailed information about an address, including geographic coordinates.
    
    Args:
        request: HTTP request containing address query parameter
        
    Returns:
        JSON response with address details in English and Chinese, plus geospatial information
    """ 
    address = request.query_params.get("address", "")
    if not address:
        return Response({"error": "Address parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    number = 1
    api_url = f"https://www.als.gov.hk/lookup?q={address}&n={number}"
    headers = {"Accept": "application/json"} 

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        try:
            data = response.json()
            if data and 'SuggestedAddress' in data and len(data['SuggestedAddress']) > 0:
                result = data['SuggestedAddress'][0]['Address']['PremisesAddress']
                eng_address = result.get("EngPremisesAddress", {})
                chi_address = result.get("ChiPremisesAddress", {})
                geospatial_info = result.get("GeospatialInformation", {})
                geo_address = result.get("GeoAddress", "")
                return Response({
                    "EnglishAddress": {
                        "BuildingName": eng_address.get("BuildingName", ""),
                        "EstateName": eng_address.get("EngEstate", {}).get("EstateName", ""),
                        "StreetName": eng_address.get("EngStreet", {}).get("StreetName", ""),
                        "BuildingNo": eng_address.get("EngStreet", {}).get("BuildingNoFrom", ""),
                        "District": eng_address.get("EngDistrict", {}).get("DcDistrict", ""),
                        "Region": eng_address.get("Region", ""),
                    },
                    "ChineseAddress": {
                        "BuildingName": chi_address.get("BuildingName", ""),
                        "EstateName": chi_address.get("ChiEstate", {}).get("EstateName", ""),
                        "StreetName": chi_address.get("ChiStreet", {}).get("StreetName", ""),
                        "BuildingNo": chi_address.get("ChiStreet", {}).get("BuildingNoFrom", ""),
                        "District": chi_address.get("ChiDistrict", {}).get("DcDistrict", ""),
                        "Region": chi_address.get("Region", ""),
                    },
                    "GeospatialInformation": {
                        "Latitude": geospatial_info.get("Latitude", None),
                        "Longitude": geospatial_info.get("Longitude", None),
                        "Northing": geospatial_info.get("Northing", None),
                        "Easting": geospatial_info.get("Easting", None),
                        "GeoAddress": geo_address
                    }
                })
            else:
                return Response({"error": "No results found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid JSON response from API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except requests.HTTPError as e:
        return Response({"error": f"HTTP Error: {e.response.status_code}"}, status=e.response.status_code)
    except requests.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#------------------------------------------------------------------------------
# Accommodation Management
#------------------------------------------------------------------------------
@extend_schema(
    summary="Add Accommodation",
    description="Add new accommodation information. Requires API key authentication for POST.",
    request=AddAccommodationSerializer,
    parameters=API_KEY_PARAMETER,
    responses={
        201: SuccessResponseSerializer,
        400: ErrorResponseSerializer,
        401: OpenApiResponse(description="API key authentication failed"),
        403: OpenApiResponse(description="Permission denied"),
        500: ErrorResponseSerializer
    }
)
@api_view(['GET', 'POST']) 
@authentication_classes([UniversityAPIKeyAuthentication])
@permission_classes([UniversityAccessPermission])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer]) 
def add_accommodation(request):
    """
    Add new accommodation information.

    supports both GET and POST methods.
    - GET: Returns the accommodation form for adding new accommodation.
    - POST: Processes the form submission to add new accommodation information.
    """
    is_api_request = request.accepted_renderer.format == 'json'
    
    # GET method returns the accommodation form
    if request.method == 'GET':
        if is_api_request:
            return Response({
                "success": True,
                "message": "To add accommodation, make a POST request with the required data",
                "required_fields": {
                    "title": "Accommodation title",
                    "type": "Accommodation type (HOUSE, APARTMENT, etc.)",
                    "description": "Description of the accommodation",
                    "beds": "Number of beds",
                    "bedrooms": "Number of bedrooms",
                    "available_from": "yyyy-mm-dd",
                    "available_to": "yyyy-mm-dd",
                    "building_name": "the name of the building",
                    "room_number": "room number",
                    "floor_number": "floor number",
                    "flat_number": "flat number",
                    "contact_name": "contact name",
                    "contact_phone": "contact phone number",
                    "contact_email": "user@example.com"
                }
            })
        form = AccommodationForm()
        return Response({'form': form}, template_name='accommodation/add_accommodation.html')
    
    # POST method need API key authentication
    if not hasattr(request, 'auth') or not request.auth:
        # check if the request has an API key in the header or query parameters
        api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
        
        # record the API key for debugging
        print(f"[DEBUG-Backend] Received API key: {api_key}")
        
        if not api_key:
            return Response(
                {"success": False, "message": "API key is required for adding accommodations"},
                status=status.HTTP_401_UNAUTHORIZED,
                content_type= 'application/json'
            )
        
        try:
            api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
            print(f"[DEBUG-Backend] Found API key object: {api_key_obj}, University: {api_key_obj.university.name}")
            
            request.user = api_key_obj.university
            request.auth = api_key_obj
            
        except UniversityAPIKey.DoesNotExist:
            print(f"[DEBUG-Backend] API key not found in database or inactive: {api_key}")
            return Response(
                {"success": False, "message": "Invalid API key"},
                status=status.HTTP_401_UNAUTHORIZED,
                content_type= 'application/json'
            )
        
    print(f"[DEBUG-Backend] Authentication successful: University {request.user.name} ({request.user.code})")
    
    university = request.user
    
    serializer = AddAccommodationSerializer(data=request.data)
    if serializer.is_valid():
        accommodation = Accommodation()
        fields = ['title', 'description', 'type', 'price', 'beds', 
                 'bedrooms', 'available_from', 'available_to',
                 'contact_name','contact_phone', 'contact_email',
                 'room_number', 'floor_number', 'flat_number']
        for field in fields:
            if field in serializer.validated_data:
                setattr(accommodation, field, serializer.validated_data[field])
        address = serializer.validated_data['building_name']
        api_url = f"https://www.als.gov.hk/lookup?q={address}&n=1"
        headers = {"Accept": "application/json"}
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data and 'SuggestedAddress' in data and len(data['SuggestedAddress']) > 0:
                result = data['SuggestedAddress'][0]['Address']['PremisesAddress']
                geospatial_info = result.get("GeospatialInformation", {})
                eng_address = result.get("EngPremisesAddress", {})
                accommodation.latitude = geospatial_info.get("Latitude", 0.0)
                accommodation.longitude = geospatial_info.get("Longitude", 0.0)
                accommodation.geo_address = result.get("GeoAddress", "")
                accommodation.building_name = eng_address.get("BuildingName", "")
                accommodation.estate_name = eng_address.get("EngEstate", {}).get("EstateName", "")
                accommodation.street_name = eng_address.get("EngStreet", {}).get("StreetName", "")
                accommodation.building_no = eng_address.get("EngStreet", {}).get("BuildingNoFrom", "")
                accommodation.district = eng_address.get("EngDistrict", {}).get("DcDistrict", "")
                accommodation.region = eng_address.get("Region", "")

                # check if the accommodation already exists
                room_number = serializer.validated_data.get('room_number')
                floor_number = serializer.validated_data.get('floor_number')
                flat_number = serializer.validated_data.get('flat_number')
                geo_address = result.get("GeoAddress", "")

                university = request.user
                
                duplicate_accommodations = Accommodation.objects.filter(
                    geo_address=geo_address,
                    room_number=room_number,
                    floor_number=floor_number,
                    flat_number=flat_number
                )
                if duplicate_accommodations.exists():
                    try:
                        duplicate_accommodation = duplicate_accommodations.first()
                        
                        # Check whether this university has been associated with the accommodation
                        if duplicate_accommodation.affiliated_universities.filter(id=university.id).exists():
                            return Response({
                                "success": False,
                                "message": f"{university.name} is already associated with this accommodation"
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Add the university to the list of associated universities for accommodation
                        duplicate_accommodation.affiliated_universities.add(university)
                        
                        return Response({
                            "success": True,
                            "message": f"Successfully associated {university.name} with accommodation '{duplicate_accommodation.title}'",
                            "id": duplicate_accommodation.id
                        })
                    
                    except Accommodation.DoesNotExist:
                        return Response({
                            "success": False,
                            "message": "Accommodation doesn't exist"
                        }, status=status.HTTP_404_NOT_FOUND)
            
                    # return Response(
                    #     {"success": False, "message": "This accommodation information already exists. The same combination of room number, floor, unit number and address has already been recorded in the system. If is the same accommodation, you can associate it with your university."},
                    #     status=status.HTTP_400_BAD_REQUEST
                    # )
                
                try:
                    accommodation.save()
                    
                    # add the university to the accommodation's affiliated universities
                    accommodation.affiliated_universities.add(university)
                    
                    print(f"[DEBUG-Backend] The accommodation was successfully preserved: ID={accommodation.id}, titile={accommodation.title}")
                    return Response(
                        {"success": True, "message": "Accommodation added successfully!", "id": accommodation.id}, 
                        status=status.HTTP_201_CREATED
                    )
                except Exception as e:
                    print(f"[DEBUG-Backend] An error occurred when saving the accommodation: {str(e)}")
                    return Response(
                        {"success": False, "message": f"Error saving accommodation: {str(e)}"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                print("[DEBUG-Backend] The address API did not return a valid address")
                return Response(
                    {"success": False, "message": "Could not geocode the provided address. Please provide a valid Hong Kong address."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except requests.RequestException as e:
            print(f"[DEBUG-Backend] Address API request error: {str(e)}")
            return Response(
                {"success": False, "message": f"Error fetching geolocation: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        print(f"[DEBUG-Backend] Form validation failed: {serializer.errors}")
        return Response(
            {"success": False, "errors": serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    summary="Delete Accommodation",
    description=(
        "Delete an accommodation by ID using DELETE method. If the accommodation is associated with multiple universities, "
        "this will remove the current university's association instead of deleting the accommodation completely."
    ),
    parameters=[
        OpenApiParameter(name="id", location=OpenApiParameter.QUERY, description="Accommodation ID to delete", type=int, required=True),
        OpenApiParameter(name="X-API-Key", location=OpenApiParameter.HEADER, description="API key for authentication", type=str, required=True)
    ],
    responses={
        200: SuccessResponseSerializer,
        400: ErrorResponseSerializer,
        401: OpenApiResponse(description="API key authentication failed"),
        403: OpenApiResponse(description="Not allowed to delete this accommodation"),
        404: ErrorResponseSerializer
    }
)
@api_view(['DELETE'])
@parser_classes([JSONParser])
@renderer_classes([JSONRenderer])
@authentication_classes([UniversityAPIKeyAuthentication])
@permission_classes([UniversityAccessPermission])
def delete_accommodation(request):
    """
    Delete an accommodation by ID or remove university association.

    - If the accommodation is only associated with the current university, it will be completely deleted.
    - If the accommodation is associated with multiple universities, only the association with the current university will be removed.

    Args:
        request: HTTP DELETE request with query parameter "id"

    Returns:
        - JSON confirmation message on success
        - JSON error message on failure
    """
    # 获取 API Key 和验证大学身份
    university = request.user
    if not university or not hasattr(university, 'id'):
        return Response(
            {"success": False, "message": "Authentication failed. Valid API key is required."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # 获取宿舍 ID
    accommodation_id = request.query_params.get('id')
    if not accommodation_id:
        return Response(
            {"success": False, "message": "'id' query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # 获取宿舍对象
        accommodation = get_object_or_404(Accommodation, id=accommodation_id)

        # 检查是否与当前大学关联
        if not accommodation.affiliated_universities.filter(id=university.id).exists():
            return Response(
                {"success": False, "message": f"{university.name} is not associated with this accommodation."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 检查关联大学的数量
        affiliated_count = accommodation.affiliated_universities.count()
        title = accommodation.title

        if affiliated_count > 1:
            # 如果有多个大学关联，只移除当前大学的关联
            accommodation.affiliated_universities.remove(university)
            return Response(
                {"success": True, "message": f"Removed {university.name}'s association with accommodation '{title}'. The accommodation is still available to other universities."},
                status=status.HTTP_200_OK
            )
        else:
            # 如果只有一个大学关联，删除宿舍
            accommodation.delete()
            return Response(
                {"success": True, "message": f"Accommodation '{title}' has been completely deleted."},
                status=status.HTTP_200_OK
            )

    except Accommodation.DoesNotExist:
        return Response(
            {"success": False, "message": "Accommodation not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"success": False, "message": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(
    summary="List Accommodations",
    description="List all accommodations with optional filters",
    parameters=[
        OpenApiParameter(name="type", description="Accommodation type", type=str, required=False,enum=["APARTMENT", "HOUSE", "HOSTEL"]),
        OpenApiParameter(name="region", description="Region", type=str, required=False),
        OpenApiParameter(name="available_from", description="Available from date (yyyy-MM-DD)", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="available_to", description="Available to date (yyyy-MM-DD)", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="min_beds", description="Minimum beds", type=int, required=False),
        OpenApiParameter(name="min_bedrooms", description="Minimum bedrooms", type=int, required=False),
        OpenApiParameter(name="max_price", description="Maximum price", type=float, required=False),
        OpenApiParameter(name="distance", description="Maximum distance from Campus (if Campus not provide, default to HKU_main)", type=float, required=False),
        OpenApiParameter(name="order_by_distance", description="Sort by distance", type=bool, required=False),
        OpenApiParameter(
            name="campus",
            description=(
                "Specify the campus location to calculate distances from. "
                "Valid values: 'HKU_main', 'HKU_sassoon', 'HKU_swire', 'HKU_kadoorie', 'HKU_dentistry', 'HKUST', 'CUHK'. "
                "Defaults to 'HKU_main' if not provided."
            ),
            type=OpenApiTypes.STR,
            required=False,
        ),
        OpenApiParameter(
            name="user_id",
            description="User ID to filter accommodations by university affiliation",
            type=OpenApiTypes.STR,
            required=False,
        ),
        OpenApiParameter(
            name="order_by",
            description="Specify sorting order. Valid values: 'distance', 'price_asc', 'price_desc', 'rating', 'beds'.",
            type=OpenApiTypes.STR,
            required=False,
        ),
        OpenApiParameter(name="reservation_start", description="Reservation start date (yyyy-MM-DD)", type=OpenApiTypes.DATE, required=True),
        OpenApiParameter(name="reservation_end", description="Reservation end date (yyyy-MM-DD)", type=OpenApiTypes.DATE, required=True),
    ] + API_KEY_PARAMETER,
    responses={
        200: AccommodationListResponseSerializer,
    },
)
@api_view(['GET'])
def list_accommodation(request):
    """
    List all accommodations with optional filters.

    Supports various filtering options including accommodation type, region, availability dates,
    minimum beds/bedrooms, maximum price, and maximum distance from HKU.
    Distance calculation uses the Haversine formula.

    If user_id is provided, only shows accommodations affiliated with the user's university.

    If reservation_start and reservation_end are provided, only shows accommodations available during that period.
    """
    accommodations = Accommodation.objects.all()
    
    print(f"[DEBUG-Backend] Total number of accommodations before filter: {accommodations.count()}")
    
    # Get api from request header or query parameters to identify the specialist user
    api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
    is_specialist = False
    specialist_university = None

    # Output the where api is sent from
    if api_key:
        if 'HTTP_X_API_KEY' in request.META:
            print(f"[DEBUG-Backend] API Key from header: {api_key}")
        else:
            print(f"[DEBUG-Backend] API Key from query_params: {api_key}")
    
    if api_key:
        try:
            api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
            specialist_university = api_key_obj.university
            is_specialist = True
            
            university_name = specialist_university.name
            university_id = specialist_university.id
            print(f"[DEBUG-Backend] Successfully verified the expert's identity: University = {university_name}, ID={university_id}")
            
            affiliated_count = Accommodation.objects.filter(affiliated_universities=specialist_university).count()
            print(f"[DEBUG-Backend] The number of accommodations associated with this university: {affiliated_count}")
        except UniversityAPIKey.DoesNotExist:
            print(f"[DEBUG-Backend] Invalid API Key: {api_key}")
    else:
        print("[DEBUG-Backend] No API Key is provided. Student user view.")
    
    if not is_specialist:
        print("[DEBUG-Backend] Student User view - show accommodations with available periods")
    else:
        print(f"[DEBUG-Backend] Specialist - only show {specialist_university.name}'s accommodations (including reserved)")
        accommodations = accommodations.filter(affiliated_universities=specialist_university)
    
    building_name = request.query_params.get("building_name", "")
    accommodation_type = request.query_params.get("type", "")
    region = request.query_params.get("region", "")
    available_from = request.query_params.get("available_from", "")
    available_to = request.query_params.get("available_to", "")
    min_beds = request.query_params.get("min_beds", "")
    min_bedrooms = request.query_params.get("min_bedrooms", "")
    max_price = request.query_params.get("max_price", "")
    max_distance = request.query_params.get("distance", "")
    order_by = request.query_params.get("order_by", "")
    order_by_distance = request.query_params.get("order_by_distance", "false").lower() == "true"
    campus = request.query_params.get("campus", "HKU_main")  # Default to "HKU_main" campus
    user_id = request.query_params.get("user_id", "")
    reservation_start = request.query_params.get("reservation_start", "")
    reservation_end = request.query_params.get("reservation_end", "")
        
    # if user_id is provided, check if it is valid
    if user_id:
        # check if the user_id is matching the format
        if not (user_id.count('_') == 1 and any(user_id.upper().startswith(code.upper() + "_") for code in ["HKU", "HKUST", "CUHK"])):
            return Response(
                {"success": False, "message": "Invalid User ID format. Please use format like HKU_12345678."},
                status=status.HTTP_400_BAD_REQUEST
            )
        university = get_university_from_user_id(user_id)
        if university:
            # only show accommodations affiliated with the user's university
            accommodations = accommodations.filter(affiliated_universities=university)
    
    
    if campus not in CAMPUS_LOCATIONS:
        campus = "HKU_main"  # Default to "HKU_main" if campus is invalid
    # Get selected campus coordinates
    campus_coords = CAMPUS_LOCATIONS[campus]
    campus_latitude = campus_coords["latitude"]
    campus_longitude = campus_coords["longitude"]
    # print(f"[DEBUG-Backend] Campus Coordinates: {campus_latitude}, {campus_longitude}")
    
    if accommodation_type:
        accommodations = accommodations.filter(type=accommodation_type)
    
    if region:
        accommodations = accommodations.filter(region=region)

    if available_from and available_to:
        available_from = parse_date(available_from)
        available_to = parse_date(available_to)
        
        print(f"[DEBUG-Backend] User filter with date: from {available_from} to {available_to}")
                
        if available_from and available_to:
            original_count = accommodations.count()
            
            accommodations = accommodations.filter(
                Q(available_from__lte=available_from) & Q(available_to__gte=available_to)
            )
            print(f"[DEBUG-Backend] Before Date Filter has {original_count} non-reserved Accommodation, after Date Filter has {accommodations.count()} non-reserved Accommodation")
            # Debugging information to list all accommodation information
            from .utils import debug_accommodation_dates
            date_info = debug_accommodation_dates()
            print(f"[DEBUG-Backend] Accommodation available date information: {date_info}")
    if min_beds:
        accommodations = accommodations.filter(beds__gte=min_beds)

    if min_bedrooms:
        accommodations = accommodations.filter(bedrooms__gte=min_bedrooms)

    if max_price:
        accommodations = accommodations.filter(price__lte=max_price)

    # Calculate distance using Haversine formula
    accommodations = accommodations.annotate(
        distance=ExpressionWrapper(
            Func(
                Func(
                    (F('longitude') - campus_longitude) * math.pi / 180 *
                    Func((F('latitude') + campus_latitude) / 2 * math.pi / 180, function='COS'),
                    function='POW',
                    template="%(function)s(%(expressions)s, 2)"
                ) + Func(
                    (F('latitude') - campus_latitude) * math.pi / 180,
                    function='POW',
                    template="%(function)s(%(expressions)s, 2)"
                ),
                function='SQRT',
            ) * 6371,  # Earth radius (km)
            output_field=FloatField(),
        )
    )
    if max_distance:
        max_distance = float(max_distance)
        accommodations = accommodations.filter(distance__lte=max_distance)

    if reservation_start and reservation_end:
        reservation_start = parse_date(reservation_start)
        reservation_end = parse_date(reservation_end)
        
        if reservation_start and reservation_end:
            print(f"[DEBUG-Backend] Filtering reservation date range: {reservation_start} to {reservation_end}")
            
            # Get original count
            original_count = accommodations.count()
            
            # Exclude accommodations with overlapping reservations
            unavailable_accommodation_ids = []
            for accommodation in accommodations:
                if not accommodation.is_available(reservation_start, reservation_end):
                    unavailable_accommodation_ids.append(accommodation.id)
            
            accommodations = accommodations.exclude(id__in=unavailable_accommodation_ids)
            
            print(f"[DEBUG-Backend] Before date filter: {original_count} accommodations, after filter: {accommodations.count()} accommodations")
    else:
        # If no reservation dates are specified, only show accommodations with any available periods
        if not is_specialist:
            unavailable_accommodation_ids = []
            for accommodation in accommodations:
                if not accommodation.get_available_periods():
                    unavailable_accommodation_ids.append(accommodation.id)
            
            accommodations = accommodations.exclude(id__in=unavailable_accommodation_ids)
            print(f"[DEBUG-Backend] Filtered out fully booked accommodations, remaining: {accommodations.count()}")

    if order_by:
        if order_by == 'distance':
            accommodations = accommodations.order_by('distance')
        elif order_by == 'price_asc':
            accommodations = accommodations.order_by('price')
        elif order_by == 'price_desc':
            accommodations = accommodations.order_by('-price')
        elif order_by == 'rating':
            accommodations = accommodations.order_by('-rating')
        elif order_by == 'beds':
            accommodations = accommodations.order_by('-beds')
    elif order_by_distance:
        accommodations = accommodations.order_by('distance')

    print(f"[DEBUG-Backend] The number of after all filtered accommodations: {accommodations.count()}")
    
    if request.headers.get('Accept') == 'application/json' or request.query_params.get('format') == 'json':
        serializer = AccommodationListSerializer(accommodations, many=True)
        for acc_data in serializer.data:
            accommodation = Accommodation.objects.get(id=acc_data['id'])
            # 添加可用期间
            acc_data['available_periods'] = [
                {'start_date': period[0], 'end_date': period[1]} 
                for period in accommodation.get_available_periods()
            ]
            # 添加预订信息
            acc_data['reservations'] = []
            for period in accommodation.reservation_periods.all():
                acc_data['reservations'].append({
                    'id': period.id,
                    'start_date': period.start_date,
                    'end_date': period.end_date,
                    'user_id': period.user_id,
                    'contract_status': period.contract_status
                })
        return Response({'accommodations': serializer.data})
    return render(request, 'accommodation/accommodation_list.html', {
        "buildingName": building_name,
        'accommodations': accommodations,
        'accommodation_type': accommodation_type,
        'region': region,
        'available_from': available_from,
        'available_to': available_to,
        'min_beds': min_beds,
        'min_bedrooms': min_bedrooms,
        'max_price': max_price,
        'max_distance': max_distance,
        'order_by': order_by,
        'order_by_distance': order_by_distance,
        'user_id': user_id, 
        'reservation_start': reservation_start,
        'reservation_end': reservation_end,
            })

@extend_schema(
    summary="Search Accommodations",
    description="Search for accommodations with at least one filter",
    parameters=[
        OpenApiParameter(name="type", description="Accommodation type", type=str, required=False,enum=["APARTMENT", "HOUSE", "HOSTEL"]),
        OpenApiParameter(name="region", description="Region", type=str, required=False),
        OpenApiParameter(name="available_from", description="Available from date (yyyy-MM-DD)", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="available_to", description="Available to date ((yyyy-MM-DD))", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="min_beds", description="Minimum beds", type=int, required=False),
        OpenApiParameter(name="min_bedrooms", description="Minimum bedrooms", type=int, required=False),
        OpenApiParameter(name="max_price", description="Maximum price", type=float, required=False),
        OpenApiParameter(name="distance", description="Maximum distance from Campus (if Campus not provide, default to HKU_main)", type=float, required=True),
        OpenApiParameter(name="format", description="Response format", type=str, required=False),
        OpenApiParameter(
            name="campus",
            description=(
                "Specify the campus location to calculate distances from. "
                "Valid values: 'HKU_main', 'HKU_sassoon', 'HKU_swire', 'HKU_kadoorie', 'HKU_dentistry', 'HKUST', 'CUHK'. "
                "Defaults to 'HKU_main' if not provided."
            ),
            type=OpenApiTypes.STR,
            required=False,
        ),
        OpenApiParameter(
            name="user_id",
            description="User ID to filter accommodations by university affiliation",
            type=OpenApiTypes.STR,
            required=False,
        ),
    ],
    responses={
        200: MessageResponseSerializer,
        302: OpenApiResponse(description="Redirect to accommodation list")
    }
)
@api_view(['GET'])
def search_accommodation(request):
    """
    Search for accommodations with filters.

    This endpoint redirects to the list_accommodation view with the provided filters.
    If no filters are provided, it returns a search form or a message.
    
    If user_id is provided, only shows accommodations affiliated with the user's university.
    
    Args:
        request: HTTP request with search parameters
        
    Returns:
        - Redirect to list_accommodation with filters
        - HTML search form if no filters provided
        - JSON message if JSON format requested
    """
    if request.GET and any(request.GET.values()):
        query_params = request.GET.urlencode()
        if request.headers.get('Accept') == 'application/json' or request.query_params.get('format') == 'json':
            return redirect(f"{reverse('list_accommodation')}?{query_params}&format=json")
        return redirect(f"{reverse('list_accommodation')}?{query_params}")
    if request.headers.get('Accept') == 'application/json' or request.query_params.get('format') == 'json':
        return Response({"message": "Use GET with query parameters to search accommodations."})
    
    return render(request, 'accommodation/search_results.html')

@extend_schema(
    summary="Accommodation Details",
    description="View accommodation details",
    parameters=[
        OpenApiParameter(name="id", location=OpenApiParameter.PATH, description="Accommodation ID", type=int, required=True)
    ],
    responses={
        200: AccommodationDetailSerializer,
        404: ErrorResponseSerializer
    }
)
@api_view(['GET'])
def accommodation_detail(request, id):
    """
    View accommodation details.

    Retrieves and displays detailed information about a specific accommodation.

    Args:
        request: HTTP request
        id: Accommodation ID (primary key)

    Returns:
        - HTML detail page for the accommodation
        - JSON accommodation data if JSON format requested
        - 404 error if accommodation not found
    """
    try:
        accommodation = get_object_or_404(Accommodation, pk=id)
        
        # save the query string to pass to the template
        query_string = request.META.get('QUERY_STRING', '')
        
        if request.headers.get('Accept') == 'application/json' or request.query_params.get('format') == 'json':
            serializer = AccommodationDetailSerializer(accommodation)
            return Response(serializer.data)
        return render(request, 'accommodation/accommodation_detail.html', {
            'accommodation': accommodation,
            'query_string': query_string  # pass all query parameters to the template
        })
    except Accommodation.DoesNotExist:
        return Response({'error': 'Accommodation not found.'}, status=status.HTTP_404_NOT_FOUND)
    
#------------------------------------------------------------------------------
# Reservation Operations
#------------------------------------------------------------------------------
class ReservationView(GenericAPIView):
    """
    Class-based view for reservation operations.

    Handles accommodation reservation requests, which requires a user identifier
    cookie to be present in the request. The system also sends confirmation emails
    to both the student and the housing administrator.
    """
    serializer_class = ReservationResponseSerializer

    @extend_schema(
        summary="Reserve Accommodation",
        description="Reserve an accommodation for a specific time period",
        parameters=[
            OpenApiParameter(name="id", location=OpenApiParameter.QUERY, description="Accommodation ID", type=int, required=True),
            OpenApiParameter(name="User ID", location=OpenApiParameter.QUERY, 
                    description="User ID, you need to assign which school you are from,e.g. If from HKU, that is HKU_XXX, if HKUST, that is HKUST_xxx, if CUHK, CUHK_xxx", 
                    type=str, required=True),
            OpenApiParameter(name="contact_number", location=OpenApiParameter.QUERY, 
                    description="Your contact phone number for this reservation", 
                    type=str, required=True),
            OpenApiParameter(name="start_date", location=OpenApiParameter.QUERY, 
                    description="Reservation start date (YYYY-MM-DD)", 
                    type=str, required=True),
            OpenApiParameter(name="end_date", location=OpenApiParameter.QUERY, 
                    description="Reservation end date (YYYY-MM-DD)", 
                    type=str, required=True),
        ],
        responses={
            200: ReservationResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        }
    )
    def post(self, request):
        """
        Reserve an accommodation for a specific time period.
        
        Args:
            request: HTTP POST request with accommodation ID, user ID, contact number, 
                    start date and end date
                
        Returns:
            - Reservation confirmation with accommodation details
            - Error responses for various failure conditions
        """
        accommodation_id = request.query_params.get('id')
        user_id = request.query_params.get('User ID')
        contact_number = request.query_params.get('contact_number')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not accommodation_id:
            return Response({'success': False, 'message': 'Accommodation ID is required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not user_id:
            return Response({'success': False, 'message': 'User ID is required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not contact_number:
            return Response({'success': False, 'message': 'Contact number is required for reservation.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not start_date or not end_date:
            return Response({'success': False, 'message': 'Start date and end date are required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
                            
        try:
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            if not start_date or not end_date:
                return Response({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'}, 
                                status=status.HTTP_400_BAD_REQUEST)
                                
            if start_date >= end_date:
                return Response({'success': False, 'message': 'End date must be after start date.'}, 
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'message': f'Date parsing error: {str(e)}'}, 
                            status=status.HTTP_400_BAD_REQUEST)
            
        try:
            accommodation = get_object_or_404(Accommodation, id=accommodation_id)

            # Check if accommodation is available for the selected dates
            if not accommodation.is_available(start_date, end_date):
                return Response({
                    'success': False,
                    'message': f'Accommodation "{accommodation.title}" is not available for the selected dates.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get university information
            university = get_university_from_user_id(user_id)
            
            # Check if user is eligible to reserve the accommodation
            if university and accommodation.affiliated_universities.exists():
                if not accommodation.affiliated_universities.filter(id=university.id).exists():
                    university_codes = [u.code for u in accommodation.affiliated_universities.all()]
                    return Response({
                        'success': False,
                        'message': f'You are not eligible to reserve this accommodation. It is only available to students from: {", ".join(university_codes)}.'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Create new reservation record
            reservation = ReservationPeriod.objects.create(
                accommodation=accommodation,
                user_id=user_id,
                contact_number=contact_number,
                start_date=start_date,
                end_date=end_date
            )

            accommodation.save()
            
            # Send confirmation emails
            student_name = user_id.split('_')[1]
            
            # Send confirmation email to student
            student_email = f"{student_name}@example.com"  
            send_mail(
                subject="Reservation Confirmed - UniHaven",
                message=f"Hi {student_name},\n\nYour reservation for '{accommodation.title}' from {start_date} to {end_date} is confirmed.\nThank you!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
            )
            
            # Send notification email to housing specialist
            if university:
                specialist_email = university.specialist_email
                university_name = university.code
            else:
                specialist_email = "cedars@hku.hk"  # Default HKU contact
                university_name = "HKU"
                
            send_mail(
                subject=f"[UniHaven] New Reservation Alert - {university_name}",
                message=f"Dear {university_name} Housing Specialist,\n\nStudent {student_name} has reserved the accommodation: '{accommodation.title}' for the period from {start_date} to {end_date}.\nPlease follow up for contract processing.\n\nRegards,\nUniHaven System",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[specialist_email],
            )
            
            # Return success response
            serializer = AccommodationDetailSerializer(accommodation)
            return Response({
                'success': True,
                'message': f'Accommodation "{accommodation.title}" has been reserved for the period from {start_date} to {end_date}.',
                'UserID': user_id,
                'period': {'start_date': start_date, 'end_date': end_date},
                'accommodation': serializer.data
            })
        except Accommodation.DoesNotExist:
            return Response({'success': False, 'message': 'Accommodation not found.'}, 
                            status=status.HTTP_404_NOT_FOUND)

class CancellationView(GenericAPIView):
    """
    Class-based view for cancellation operations.

    Handles cancellation of accommodation reservations. The user can only cancel
    reservations they have made themselves, identified by the user_identifier cookie.
    """
    serializer_class = ReservationResponseSerializer

    @extend_schema(
        summary="Cancel Reservation",
        description="Cancel an accommodation reservation for a specific time period",
        parameters=[
            OpenApiParameter(name="id", location=OpenApiParameter.QUERY, description="Accommodation ID", type=int, required=True),
            OpenApiParameter(name="User ID", location=OpenApiParameter.QUERY, 
                             description="User ID, you need to assign which school you are from,e. if you from HKU, that is HKU_XXX, if HKUST, that is HKUST_xxx, if CUHK, CUHK_xxx", 
                             type=str, required=True),
            OpenApiParameter(name="reservation_id", location=OpenApiParameter.QUERY, 
                             description="ID of the reservation period to cancel", 
                             type=int, required=True)
        ],
        responses={
            200: ReservationResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        }
    )
    def put(self, request):
        """Cancel an accommodation reservation using query parameter id."""
        accommodation_id = request.query_params.get('id')
        user_id = request.query_params.get('User ID')
        reservation_id = request.query_params.get('reservation_id')

        if not accommodation_id:
            return Response({'success': False, 'message': 'Accommodation ID is required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not user_id:
            return Response({'success': False, 'message': 'User ID is required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not reservation_id:
            return Response({'success': False, 'message': 'Reservation ID is required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
                            
        try:
            accommodation = get_object_or_404(Accommodation, id=accommodation_id)
            
            try:
                reservation = ReservationPeriod.objects.get(id=reservation_id, accommodation=accommodation)
            except ReservationPeriod.DoesNotExist:
                return Response({'success': False, 'message': 'Reservation not found.'}, 
                                status=status.HTTP_404_NOT_FOUND)
                                
            # Check if the reservation belongs to the user
            if reservation.user_id != user_id:
                return Response({
                    'success': False, 
                    'message': 'You can only cancel your own reservations.'
                }, status=status.HTTP_403_FORBIDDEN)
                
            # Check the contract status and user roles
            # Get API key to determine if user is a specialist
            api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
            is_specialist = False
            
            if api_key:
                try:
                    api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
                    is_specialist = True
                except UniversityAPIKey.DoesNotExist:
                    is_specialist = False
            
            # If a contract has been signed and the user is not an expert, cancellation is not allowed
            if reservation.contract_status and not is_specialist:
                return Response({
                    'success': False,
                    'message': 'This reservation has a signed contract and cannot be cancelled by students. Please contact housing office for assistance.'
                }, status=status.HTTP_403_FORBIDDEN)
                
            # Get university information
            university = get_university_from_user_id(user_id)
            
            # Check user permissions
            if university and accommodation.affiliated_universities.exists():
                if not accommodation.affiliated_universities.filter(id=university.id).exists():
                    university_codes = [u.code for u in accommodation.affiliated_universities.all()]
                    return Response({
                        'success': False,
                        'message': f'You are not affiliated with this accommodation. It is only available to students from: {", ".join(university_codes)}.'
                    }, status=status.HTTP_403_FORBIDDEN)
                    
            # Store date information for email
            start_date = reservation.start_date
            end_date = reservation.end_date
            
            # Delete reservation
            reservation.delete()
            
            # Special notifications will be sent for cases where signed reservations are cancelled by experts
            message_suffix = ""
            if reservation.contract_status and is_specialist:
                message_suffix = " Note: This reservation had a signed contract and was cancelled by housing office."
            
            # Check if there are other reservations
            if not ReservationPeriod.objects.filter(accommodation=accommodation).exists():
                accommodation.save()
                
            # Send confirmation email
            student_name = user_id.split('_')[1]
            student_email = f"{student_name}@example.com"
            send_mail(
                subject="Reservation Cancelled - UniHaven",
                message=f"Hi {student_name},\n\nYour reservation for '{accommodation.title}' from {start_date} to {end_date} has been cancelled.{message_suffix}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
            )

            # Send notification to specialist
            if university:
                specialist_email = university.specialist_email
                university_name = university.code
            else:
                specialist_email = "cedars@hku.hk"
                university_name = "HKU"
                
            send_mail(
                subject="[UniHaven] Reservation Cancelled",
                message=f"Dear {university_name},\n\nStudent {student_name} has cancelled their reservation for '{accommodation.title}' from {start_date} to {end_date}.{message_suffix}\nNo further action is required.\n\nRegards,\nUniHaven System",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[specialist_email],
            )
            
            # Return success response
            serializer = AccommodationDetailSerializer(accommodation)
            return Response({
                'success': True,
                'message': f'Reservation for accommodation "{accommodation.title}" from {start_date} to {end_date} has been canceled.{message_suffix}',
                'UserID': user_id,
                'accommodation': serializer.data
            })
                
        except Accommodation.DoesNotExist:
            return Response({'success': False, 'message': 'Accommodation not found.'}, 
                            status=status.HTTP_404_NOT_FOUND)

class RatingView(GenericAPIView):
    """
    A view for rating accommodations

    """
    serializer_class = RatingSerializer

    @extend_schema(
        summary="Rate Accommodation",
        description="Rate an accommodation with a value between 0 and 5. Requires userid and rating as query parameters.",
        parameters=[
            OpenApiParameter(
                name="rating",
                location=OpenApiParameter.QUERY,
                description="Rating value (0 to 5)",
                type=int,
                required=True,
            ),
            OpenApiParameter(
                name="userid",
                location=OpenApiParameter.QUERY,
                description="Unique identifier for the user",
                type=str,
                required=True,
            )
        ],
        request=None, 
        responses={
            200: SuccessResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        }
    )
    def post(self, request, accommodation_id):
        """Rate an accommodation with userid verification"""
        user_id = request.query_params.get('userid')
        if not user_id:
            return Response(
                {"success": False, "message": "User ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        rating_str = request.query_params.get('rating')
        if not rating_str:
            return Response(
                {"success": False, "message": "Rating parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            rating_value = int(rating_str)
            if not 0 <= rating_value <= 5:
                raise ValueError("Rating must be between 0 and 5.")
        except ValueError:
            return Response(
                {"success": False, "message": "Invalid rating. Must be an integer between 0 and 5."},
                status=status.HTTP_400_BAD_REQUEST
            )
        accommodation = get_object_or_404(Accommodation, id=accommodation_id)
        if not ReservationPeriod.objects.filter(accommodation=accommodation, user_id=user_id).exists():
            return Response(
                {"success": False, "message": "You can only rate accommodations you have reserved."},
                status=status.HTTP_403_FORBIDDEN
            )
        if AccommodationRating.objects.filter(
            accommodation=accommodation, user_identifier=user_id
        ).exists():
            return Response(
                {"success": False, "message": "You have already rated this accommodation."},
                status=status.HTTP_400_BAD_REQUEST
            )
        AccommodationRating.objects.create(
            accommodation=accommodation,
            user_identifier=user_id,
            rating=rating_value
        )
        accommodation.rating_sum += rating_value
        accommodation.rating_count += 1
        accommodation.rating = (
            round(accommodation.rating_sum / accommodation.rating_count, 1)
            if accommodation.rating_count > 0
            else 0.0
        )
        accommodation.save()
        accommodation_serializer = AccommodationDetailSerializer(accommodation)
        return Response(
            {
                "success": True,
                "message": "Rating submitted successfully.",
                "accommodation": accommodation_serializer.data
            },
            status=status.HTTP_200_OK
        )

# Create view functions from class-based views
reserve_accommodation = ReservationView.as_view()
cancel_reservation = CancellationView.as_view()
rate_accommodation = RatingView.as_view()

@api_view(['GET'])
@extend_schema(responses=TemplateResponseSerializer)
@renderer_classes([TemplateHTMLRenderer])
def api_key_management(request):
    """ATest whether the API key is valid"""
    return Response(template_name='accommodation/api_key_management.html')

@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@extend_schema(responses=TemplateResponseSerializer)
def manage_accommodations(request):
    """The dormitory administrator page view is used to delete accommodation"""
    return Response(template_name='accommodation/manage_accommodations.html')

@api_view(['GET'])
@extend_schema(responses=ApiKeyTestResponseSerializer)
@authentication_classes([UniversityAPIKeyAuthentication])
def test_api_key(request):
    """Test whether the API key is valid"""
    university = request.user
    return Response({
        "success": True,
        "message": "Valid API key",
        "university": university.name,
        "code": university.code
    })

@extend_schema(
    summary="Check Duplicate Accommodation",
    description="Check if similar accommodation already exists in the system",
    parameters=[
        OpenApiParameter(name="address", location=OpenApiParameter.QUERY, description="Address to check", type=str, required=True),
        OpenApiParameter(name="floor_number", location=OpenApiParameter.QUERY, description="Floor number", type=str, required=False),
        OpenApiParameter(name="flat_number", location=OpenApiParameter.QUERY, description="Flat/Unit number", type=str, required=False),
        OpenApiParameter(name="room_number", location=OpenApiParameter.QUERY, description="Room number", type=str, required=False),
    ] + API_KEY_PARAMETER,
    responses={
        200: DuplicateAccommodationResponseSerializer,
        400: ErrorResponseSerializer,
        401: OpenApiResponse(description="API key authentication failed"),
    }
)
@api_view(['GET'])
@authentication_classes([UniversityAPIKeyAuthentication])
def check_duplicate_accommodation(request):
    """
    Check for duplicate accommodations.
    
    Search for similar accommodations that may exist in the system based on the Building Name and unit details.
    """
    building_name = request.query_params.get('building_name', '')
    floor_number = request.query_params.get('floor_number', '')
    flat_number = request.query_params.get('flat_number', '')
    room_number = request.query_params.get('room_number', '')
    
    if not building_name:
        return Response(
            {"success": False, "message": "Building name is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get the current university from the API key
    university = request.user
    
    api_url = f"https://www.als.gov.hk/lookup?q={building_name}&n=1"
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data and 'SuggestedAddress' in data and len(data['SuggestedAddress']) > 0:
            result = data['SuggestedAddress'][0]['Address']['PremisesAddress']
            geo_address = result.get("GeoAddress", "")
            
            exact_matches = Accommodation.objects.filter(
                geo_address=geo_address,
                floor_number=floor_number,
                flat_number=flat_number,
                room_number=room_number
            )
            
            # Check if the university is already associated with any exact matches
            for match in exact_matches:
                if match.affiliated_universities.filter(id=university.id).exists():
                    return Response({
                        "success": False,
                        "message": "Your university is already associated with an identical accommodation",
                        "already_associated": True,
                        "accommodation_id": match.id,
                        "accommodation_title": match.title
                    })
            
            if not exact_matches.exists():
                query = Q(geo_address=geo_address)
                
                if floor_number:
                    query &= Q(floor_number=floor_number)
                if flat_number:
                    query &= Q(flat_number=flat_number)
                if room_number:
                    query &= Q(room_number=room_number)
                
                partial_matches = Accommodation.objects.filter(query)
                potential_duplicates = partial_matches
            else:
                potential_duplicates = exact_matches
            
            if potential_duplicates.exists():
                duplicates_data = []
                for acc in potential_duplicates:
                    # Get the list of affiliated universities and their codes
                    universities = [uni.name for uni in acc.affiliated_universities.all()]
                    university_codes = [uni.code for uni in acc.affiliated_universities.all()]
                    
                    # Check if current university is already associated
                    already_associated = acc.affiliated_universities.filter(id=university.id).exists()
                    
                    duplicates_data.append({
                        'id': acc.id,
                        'title': acc.title,
                        'geo_address': acc.geo_address,
                        'formatted_address': acc.formatted_address(),
                        'floor_number': acc.floor_number,
                        'flat_number': acc.flat_number,
                        'room_number': acc.room_number,
                        'universities': universities,
                        'university_codes': university_codes,
                        'already_associated': already_associated  # Add this flag
                    })
                
                return Response({
                    "success": True,
                    "message": "Found potential duplicate accommodations",
                    "duplicates": duplicates_data
                })
            else:
                return Response({
                    "success": True,
                    "message": "No duplicate accommodations found",
                    "duplicates": []
                })
        else:
            return Response({
                "success": False, 
                "message": "Could not geocode the address"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except requests.RequestException as e:
        return Response({
            "success": False, 
            "message": f"Error checking for duplicates: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Link to Existing Accommodation",
    description="Link a university (identified by API key) to an existing accommodation",
    parameters=[

        OpenApiParameter(name="id", location=OpenApiParameter.PATH, description="Accommodation ID to link to", type=int, required=True),
    ] + API_KEY_PARAMETER,
    responses={
        200: SuccessResponseSerializer,
400: ErrorResponseSerializer,
        401: OpenApiResponse(description="API key authentication failed"),
        404: ErrorResponseSerializer
    }
)
@api_view(['POST'])
@extend_schema(responses=LinkAccommodationResponseSerializer)
@authentication_classes([UniversityAPIKeyAuthentication])
def link_to_accommodation(request, id):
    """
    link the university (identified by API key) to an existing accommodation.
    API Key is required for authentication.
    """
    university = request.user
    
    try:
        accommodation = Accommodation.objects.get(id=id)
        
        # Check whether this university has been associated with this accommodation
        if accommodation.affiliated_universities.filter(id=university.id).exists():
            return Response({
                "success": False,
                "message": f"{university.name} is already associated with this accommodation"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # add the university to the accommodation's affiliated universities
        accommodation.affiliated_universities.add(university)
        
        return Response({
            "success": True,
            "message": f"Successfully associated {university.name} with accommodation '{accommodation.title}'",
            "id": accommodation.id
        })
        
    except Accommodation.DoesNotExist:
        return Response({
            "success": False,
            "message": "Accommodation doesn't exist"
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@renderer_classes([TemplateHTMLRenderer])
def view_reservations(request):
    """
    View to display all reservations for a specific user.
    
    GET: Shows a form to enter User ID
    POST: Shows all reservations for the provided User ID
    """
    if request.method == 'POST':
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'User ID is required'}, template_name='accommodation/view_reservations.html')
        
        # Validate user ID format
        if not (user_id.count('_') == 1 and any(user_id.upper().startswith(code.upper() + "_") for code in ["HKU", "HKUST", "CUHK"])):
            return Response({'error': 'Invalid User ID format. Please use format like HKU_12345678.'}, template_name='accommodation/view_reservations.html')
        
        # Query reservations through ReservationPeriod instead of using the userID field of accommodation
        reservation_periods = ReservationPeriod.objects.filter(user_id=user_id).select_related('accommodation')
        accommodations = []
        seen_ids = set()
        
        # Group reservation periods under their respective accommodation objects
        for period in reservation_periods:
            accommodation = period.accommodation
            if accommodation.id not in seen_ids:
                seen_ids.add(accommodation.id)
                accommodations.append(accommodation)
                # Add the user's reservation periods to the accommodation object
                accommodation.user_reservation_periods = []
            
            # Find the current accommodation object and add the reservation period
            for acc in accommodations:
                if acc.id == accommodation.id:
                    acc.user_reservation_periods.append(period)
        
        return Response({'reservations': accommodations, 'user_id': user_id}, template_name='accommodation/view_reservations.html')
    else:
        # Show a form to enter User ID
        return Response({}, template_name='accommodation/view_reservations.html')
    
class UpdateAccommodationView(GenericAPIView):
    """
    API View to update accommodation information.

    Allows updating of accommodation information if the accommodation is associated
    with the user's university (determined by API key authentication).
    """
    serializer_class = AddAccommodationSerializer  # Use the same serializer as for creating accommodations

    @extend_schema(
        summary="Update Accommodation",
        description="Update information of an existing accommodation by ID. Requires API key authentication.",
        parameters=[
            OpenApiParameter(name="id", location=OpenApiParameter.PATH, description="Accommodation ID", type=int, required=True)
        ] + API_KEY_PARAMETER,
        request=AddAccommodationSerializer,
        responses={
            200: SuccessResponseSerializer,
            400: ErrorResponseSerializer,
            401: OpenApiResponse(description="API key authentication failed"),
            403: OpenApiResponse(description="Not allowed to update this accommodation"),
            404: ErrorResponseSerializer
        }
    )
    def put(self, request, id):
        """
        Update an accommodation by ID.

        Args:
            request: HTTP PUT request with updated accommodation data.
            id: ID of the accommodation to update.

        Returns:
            JSON response with success message and updated accommodation data.
        """
        try:
            # Get the accommodation object
            accommodation = get_object_or_404(Accommodation, id=id)
            if not hasattr(request, 'auth') or not request.auth:
                # check if the request has an API key in the header or query parameters
                api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
                
                # record the API key for debugging
                print(f"[DEBUG-Backend] Received API key: {api_key}")
                
                if not api_key:
                    return Response(
                        {"success": False, "message": "API key is required for adding accommodations"},
                        status=status.HTTP_401_UNAUTHORIZED,
                        content_type= 'application/json'
                    )
                
                try:
                    api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
                    print(f"[DEBUG-Backend] Found API key object: {api_key_obj}, University: {api_key_obj.university.name}")
                    
                    request.user = api_key_obj.university
                    request.auth = api_key_obj
                    
                except UniversityAPIKey.DoesNotExist:
                    print(f"[DEBUG-Backend] API key not found in database or inactive: {api_key}")
                    return Response(
                        {"success": False, "message": "Invalid API key"},
                        status=status.HTTP_401_UNAUTHORIZED,
                        content_type= 'application/json'
                    )
            university = request.user
            if not accommodation.affiliated_universities.filter(id=university.id).exists():
                return Response(
                    {"success": False, "message": f"{university.name} is not associated with this accommodation."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate and update accommodation information
            serializer = self.serializer_class(accommodation, data=request.data, partial=False)  # Use complete update
            if serializer.is_valid():
                updated_accommodation = serializer.save()
                updated_accommodation.affiliated_universities.add(university)  # Ensure the university remains associated

                return Response(
                    {"success": True, "message": "Accommodation updated successfully.", "accommodation": serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Accommodation.DoesNotExist:
            return Response(
                {"success": False, "message": "Accommodation not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, id):
        """
        Partially update an accommodation by ID.

        Args:
            request: HTTP PATCH request with partial accommodation data.
            id: ID of the accommodation to update.

        Returns:
            JSON response with success message and updated accommodation data.
        """
        try:
            # Get the accommodation object
            accommodation = get_object_or_404(Accommodation, id=id)

            # Verify if the current university is associated with this accommodation
            university = request.user
            if not accommodation.affiliated_universities.filter(id=university.id).exists():
                return Response(
                    {"success": False, "message": f"{university.name} is not associated with this accommodation."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate and partially update accommodation information
            serializer = self.serializer_class(accommodation, data=request.data, partial=True)  # Use partial update
            if serializer.is_valid():
                updated_accommodation = serializer.save()

                return Response(
                    {"success": True, "message": "Accommodation updated successfully.", "accommodation": serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Accommodation.DoesNotExist:
            return Response(
                {"success": False, "message": "Accommodation not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
@extend_schema(
    summary="Check Accommodation Availability",
    description="Check if an accommodation is available for specific dates",
    parameters=[
        OpenApiParameter(name="id", location=OpenApiParameter.QUERY, description="Accommodation ID", type=int, required=True),
        OpenApiParameter(name="start_date", location=OpenApiParameter.QUERY, description="Start date (YYYY-MM-DD)", type=str, required=True),
        OpenApiParameter(name="end_date", location=OpenApiParameter.QUERY, description="End date (YYYY-MM-DD)", type=str, required=True),
    ],
    responses={
        200: SuccessResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer
    }
)
@api_view(['GET'])
def check_availability(request):
    """
    Check if an accommodation is available for specific dates.
    """
    accommodation_id = request.query_params.get('id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not all([accommodation_id, start_date, end_date]):
        return Response({
            'success': False,
            'message': 'Missing required parameters.',
            'available': False
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        
        if not start_date or not end_date:
            return Response({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD.',
                'available': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if start_date >= end_date:
            return Response({
                'success': False,
                'message': 'End date must be after start date.',
                'available': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Set minimum booking duration
        MIN_BOOKING_DAYS = 1
        booking_days = (end_date - start_date).days
        if booking_days < MIN_BOOKING_DAYS:
            return Response({
                'success': False,
                'message': f'Minimum booking period is {MIN_BOOKING_DAYS} days.',
                'available': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        accommodation = get_object_or_404(Accommodation, id=accommodation_id)
        
        # Check if dates are within accommodation's available range
        if start_date < accommodation.available_from or end_date > accommodation.available_to:
            return Response({
                'success': False,
                'message': f'Dates must be within available range: {accommodation.available_from} to {accommodation.available_to}',
                'available': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if dates overlap with existing reservations
        is_available = accommodation.is_available(start_date, end_date)
        
        if is_available:
            return Response({
                'success': True,
                'message': 'Selected dates are available.',
                'available': True
            })
        else:
            return Response({
                'success': False,
                'message': 'Selected dates overlap with existing reservations.',
                'available': False
            }, status=status.HTTP_200_OK)
            
    except Accommodation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Accommodation not found.',
            'available': False
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e),
            'available': False
        }, status=status.HTTP_400_BAD_REQUEST)

# Update is_available method in Accommodation model
def is_available(self, start_date, end_date):
    """
    Check if accommodation is available for the given time period.
    """
    # Set minimum booking duration
    MIN_BOOKING_DAYS = 1
    
    # Check if booking duration meets minimum requirement
    booking_days = (end_date - start_date).days
    if booking_days < MIN_BOOKING_DAYS:
        return False
        
    # Check if dates are within accommodation's available range
    if start_date < self.available_from or end_date > self.available_to:
        return False
        
    # Check if dates overlap with existing reservations
    overlapping_reservations = self.reservation_periods.filter(
        Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
    ).exists()
    
    return not overlapping_reservations