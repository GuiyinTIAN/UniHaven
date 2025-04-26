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
from django.db.models import Q, F, Func, FloatField, ExpressionWrapper
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

from .models import Accommodation, AccommodationRating, UniversityAPIKey
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
    DeleteAccommodationRequestSerializer
)
from .utils import get_university_from_user_id
from .authentication import UniversityAPIKeyAuthentication
from .permissions import UniversityAccessPermission

#------------------------------------------------------------------------------
# Constants and Configurations
#------------------------------------------------------------------------------

# Geographic coordinates of The University of Hong Kong (used for distance calculations)
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
@parser_classes([JSONParser, FormParser, MultiPartParser])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer]) 
def add_accommodation(request):
    """
    Add new accommodation information.

    supports both GET and POST methods.
    - GET: Returns the accommodation form for adding new accommodation.
    - POST: Processes the form submission to add new accommodation information.
    """
    # GET method returns the accommodation form
    if request.method == 'GET':
        form = AccommodationForm()
        return Response({'form': form}, template_name='accommodation/add_accommodation.html')
    
    # POST method need API key authentication
    if not hasattr(request, 'auth') or not request.auth:
        # check if the request has an API key in the header or query parameters
        api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
        
        # record the API key for debugging
        print(f"DEBUG - Received API key: {api_key}")
        
        if not api_key:
            return Response(
                {"success": False, "message": "API key is required for adding accommodations"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
            print(f"DEBUG - Found API key object: {api_key_obj}, University: {api_key_obj.university.name}")
            
            request.user = api_key_obj.university
            request.auth = api_key_obj
            
        except UniversityAPIKey.DoesNotExist:
            print(f"DEBUG - API key not found in database or inactive: {api_key}")
            return Response(
                {"success": False, "message": "Invalid API key"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
    print(f"DEBUG - Authentication successful: University {request.user.name} ({request.user.code})")
    
    university = request.user
    
    serializer = AddAccommodationSerializer(data=request.data)
    if serializer.is_valid():
        accommodation = Accommodation()
        fields = ['title', 'description', 'type', 'price', 'beds', 
                 'bedrooms', 'available_from', 'available_to',
                 'contact_phone', 'contact_email',
                 'room_number', 'floor_number', 'flat_number']
        for field in fields:
            if field in serializer.validated_data:
                setattr(accommodation, field, serializer.validated_data[field])
        address = serializer.validated_data['address']
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
                
                if Accommodation.objects.filter(
                    geo_address=geo_address,
                    room_number=room_number,
                    floor_number=floor_number,
                    flat_number=flat_number
                ).exists():
                    return Response(
                        {"success": False, "message": "This accommodation information already exists. The same combination of room number, floor, unit number and address has already been recorded in the system."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    accommodation.save()
                    
                    # add the university to the accommodation's affiliated universities
                    accommodation.affiliated_universities.add(university)
                    
                    print(f"The accommodation was successfully preserved: ID={accommodation.id}, titile={accommodation.title}")
                    return Response(
                        {"success": True, "message": "Accommodation added successfully!", "id": accommodation.id}, 
                        status=status.HTTP_201_CREATED
                    )
                except Exception as e:
                    print(f"An error occurred when saving the accommodation: {str(e)}")
                    return Response(
                        {"success": False, "message": f"Error saving accommodation: {str(e)}"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                print("The address API did not return a valid address")
                return Response(
                    {"success": False, "message": "Could not geocode the provided address. Please provide a valid Hong Kong address."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except requests.RequestException as e:
            print(f"地址API请求错误: {str(e)}")
            return Response(
                {"success": False, "message": f"Error fetching geolocation: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        print(f"表单验证失败: {serializer.errors}")
        return Response(
            {"success": False, "errors": serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@extend_schema(
    summary="Delete Accommodation",
    description="Delete an accommodation by ID using POST method. Requires API key authentication.",
    request=DeleteAccommodationRequestSerializer,
    parameters=API_KEY_PARAMETER,
    responses={
        200: SuccessResponseSerializer,
        400: ErrorResponseSerializer,
        401: OpenApiResponse(description="API key authentication failed"),
        403: OpenApiResponse(description="Not allowed to delete this accommodation"),
        404: ErrorResponseSerializer
    }
)
@api_view(['POST'])
@parser_classes([JSONParser])
@renderer_classes([JSONRenderer])
@authentication_classes([UniversityAPIKeyAuthentication])
@permission_classes([UniversityAccessPermission])
def delete_accommodation(request):
    """
    Delete an accommodation by ID.

    Processes a POST request with JSON containing the accommodation ID.
    If the ID is valid and exists, the corresponding accommodation will be deleted.
    Requires API key authentication - only university systems that created the accommodation can delete it.

    Args:
        request: HTTP POST request with JSON containing "id"

    Returns:
        - JSON confirmation message on success
        - JSON error message on failure
    """
    serializer = DeleteAccommodationRequestSerializer(data=request.data)
    if serializer.is_valid():
        accommodation_id = serializer.validated_data['id']
        try:
            accommodation = Accommodation.objects.get(id=accommodation_id)
            
            title = accommodation.title
            accommodation.delete()
            return Response(
                {"success": True, "message": f"Accommodation '{title}' has been deleted."},
                status=status.HTTP_200_OK
            )
        except Accommodation.DoesNotExist:
            return Response(
                {"success": False, "message": "Accommodation not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

@extend_schema(
    summary="List Accommodations",
    description="List all accommodations with optional filters",
    parameters=[
        OpenApiParameter(name="type", description="Accommodation type", type=str, required=False),
        OpenApiParameter(name="region", description="Region", type=str, required=False),
        OpenApiParameter(name="available_from", description="Available from date", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="available_to", description="Available to date", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="min_beds", description="Minimum beds", type=int, required=False),
        OpenApiParameter(name="min_bedrooms", description="Minimum bedrooms", type=int, required=False),
        OpenApiParameter(name="max_price", description="Maximum price", type=float, required=False),
        OpenApiParameter(name="distance", description="Maximum distance from HKU (km)", type=float, required=True),
        OpenApiParameter(name="order_by_distance", description="Sort by distance", type=bool, required=False),
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
        OpenApiParameter(
            name="order_by",
            description="Specify sorting order. Valid values: 'distance', 'price_asc', 'price_desc', 'rating', 'beds'.",
            type=OpenApiTypes.STR,
            required=False,
        ),
    ],
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
    """
    accommodations = Accommodation.objects.all()
    
    # Check if the request has an API key in the header or query parameters
    api_key = request.META.get('HTTP_X_API_KEY') or request.query_params.get('api_key')
    if api_key:
        try:
            api_key_obj = UniversityAPIKey.objects.get(key=api_key, is_active=True)
            university = api_key_obj.university
            accommodations = accommodations.filter(affiliated_universities=university)
            print(f"Use API key filtering: Only display and {university.name} Related accommodation")
        except UniversityAPIKey.DoesNotExist:
            print(f"Invalid API key: {api_key}")
    
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
    user_id = request.query_params.get("user_id", "")  # 获取用户ID
    
    # 如果提供了用户ID，根据用户所属大学筛选住宿
    if user_id:
        university = get_university_from_user_id(user_id)
        if university:
            # 只显示与用户大学关联的住宿
            accommodations = accommodations.filter(affiliated_universities=university)
    
    if campus not in CAMPUS_LOCATIONS:
        campus = "HKU_main"  # Default to "HKU_main" if campus is invalid
    # Get selected campus coordinates
    campus_coords = CAMPUS_LOCATIONS[campus]
    campus_latitude = campus_coords["latitude"]
    campus_longitude = campus_coords["longitude"]
    print(f"Campus Coordinates: {campus_latitude}, {campus_longitude}")
    
    if accommodation_type:
        accommodations = accommodations.filter(type=accommodation_type)
    
    if region:
        accommodations = accommodations.filter(region=region)

    if available_from and available_to:
        try:
            available_from = parse_date(available_from)
            available_to = parse_date(available_to)
            if available_from and available_to:
                accommodations = accommodations.filter(
                    Q(available_from__lte=available_from) & Q(available_to__gte=available_to)
                )
        except ValueError:
            pass
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

    # 处理排序参数
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

    if request.headers.get('Accept') == 'application/json' or request.query_params.get('format') == 'json':
        serializer = AccommodationListSerializer(accommodations, many=True)
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
    })

@extend_schema(
    summary="Search Accommodations",
    description="Search for accommodations with at least one filter",
    parameters=[
        OpenApiParameter(name="type", description="Accommodation type", type=str, required=False),
        OpenApiParameter(name="region", description="Region", type=str, required=False),
        OpenApiParameter(name="available_from", description="Available from date", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="available_to", description="Available to date", type=OpenApiTypes.DATE, required=False),
        OpenApiParameter(name="min_beds", description="Minimum beds", type=int, required=False),
        OpenApiParameter(name="min_bedrooms", description="Minimum bedrooms", type=int, required=False),
        OpenApiParameter(name="max_price", description="Maximum price", type=float, required=False),
        OpenApiParameter(name="distance", description="Maximum distance from HKU (km)", type=float, required=True),
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
        
        # 保存所有查询参数以传递给模板
        query_string = request.META.get('QUERY_STRING', '')
        
        if request.headers.get('Accept') == 'application/json' or request.query_params.get('format') == 'json':
            serializer = AccommodationDetailSerializer(accommodation)
            return Response(serializer.data)
        return render(request, 'accommodation/accommodation_detail.html', {
            'accommodation': accommodation,
            'query_string': query_string  # 传递所有查询参数
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
        description="Reserve an accommodation using query parameter id and user id",
        parameters=[
            OpenApiParameter(name="id", location=OpenApiParameter.QUERY, description="Accommodation ID", type=int, required=True),
            OpenApiParameter(name="User ID", location=OpenApiParameter.QUERY, 
                    description="User ID, you need to assign which school you are from,e.g. If from HKU, that is HKU_XXX, if HKUST, that is HKUST_xxx, if CUHK, CUHK_xxx", 
                    type=str, required=True)
        ],
        responses={
            200: ReservationResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        }
    )
    def post(self, request):
        """
        Reserve an accommodation using query parameter id.

        Args:
            request: HTTP POST request with accommodation ID and user cookie
            
        Returns:
            - Reservation confirmation with accommodation details
            - Error responses for various failure conditions
        """
        accommodation_id = request.query_params.get('id')
        user_id = request.query_params.get('User ID')

        if not accommodation_id:
            return Response({'success': False, 'message': 'Accommodation ID is required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not user_id:
            return Response({'success': False, 'message': 'User ID is required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            accommodation = get_object_or_404(Accommodation, id=accommodation_id)

            if accommodation.reserved:
                return Response({
                    'success': False,
                    'message': f'Accommodation "{accommodation.title}" is already reserved by [{accommodation.userID}].'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取用户所属大学
            university = get_university_from_user_id(user_id)
            
            # 检查用户是否有资格预订该住宿（是否属于关联大学）
            if university and accommodation.affiliated_universities.exists():
                if not accommodation.affiliated_universities.filter(id=university.id).exists():
                    university_codes = [u.code for u in accommodation.affiliated_universities.all()]
                    return Response({
                        'success': False,
                        'message': f'You are not eligible to reserve this accommodation. It is only available to students from: {", ".join(university_codes)}.'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            accommodation.reserved = True
            accommodation.userID = user_id
            accommodation.save()
            
            student_name = student_name = user_id.split('_')[1]
            
            # 发送邮件给学生
            student_email = f"{student_name}@example.com"  
            send_mail(
                subject="Reservation Confirmed - UniHaven",
                message=f"Hi {student_name},\n\nYour reservation for '{accommodation.title}' is confirmed.\nThank you!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
            )
            
            # 发送邮件给对应大学的专家
            if university:
                specialist_email = university.specialist_email
                university_name = university.name
            else:
                specialist_email = "cedars@hku.hk"  # 默认的HKU联系人
                university_name = "HKU"
                
            send_mail(
                subject=f"[UniHaven] New Reservation Alert - {university_name}",
                message=f"Dear {university_name} Housing Specialist,\n\nStudent {student_name} has reserved the accommodation: '{accommodation.title}'.\nPlease follow up for contract processing.\n\nRegards,\nUniHaven System",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[specialist_email],
            )
            
            serializer = AccommodationDetailSerializer(accommodation)
            return Response({
                'success': True,
                'message': f'Accommodation "{accommodation.title}" has been reserved.',
                'UserID': user_id,
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
        description="Cancel an accommodation reservation using query parameter id and user id",
        parameters=[
            OpenApiParameter(name="id", location=OpenApiParameter.QUERY, description="Accommodation ID", type=int, required=True),
            OpenApiParameter(name="User ID", location=OpenApiParameter.QUERY, 
                             description="User ID, you need to assign which school you are from,e. if you from HKU, that is HKU_XXX, if HKUST, that is HKUST_xxx, if CUHK, CUHK_xxx", 
                             type=str, required=True)
        ],
        responses={
            200: ReservationResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        }
    )
    def post(self, request):
        """Cancel an accommodation reservation using query parameter id."""
        accommodation_id = request.query_params.get('id')
        user_id = request.query_params.get('User ID')

        if not accommodation_id:
            return Response({'success': False, 'message': 'Accommodation ID is required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not user_id:
            return Response({'success': False, 'message': 'User ID is required.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            accommodation = get_object_or_404(Accommodation, id=accommodation_id)

            if not accommodation.reserved:
                return Response({
                    'success': False,
                    'message': f'Accommodation "{accommodation.title}" is not reserved.'
                }, status=status.HTTP_400_BAD_REQUEST)
            if str(accommodation.userID) != user_id:
                return Response({
                    'success': False,
                    'message': f'You are not authorized to cancel this reservation. The accommodation can only be canceled by [{accommodation.userID}].'
                }, status=status.HTTP_403_FORBIDDEN)
            accommodation.reserved = False
            accommodation.userID = ""
            accommodation.save()

            student_name = user_id.split('_')[1]
            student_email = f"{student_name}@example.com"
            send_mail(
                subject="Reservation Cancelled - UniHaven",
                message=f"Hi {student_name},\n\nYour reservation for '{accommodation.title}' has been cancelled.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
            )
            specialist_email = "cedars@hku.hk"  
            send_mail(
                subject="[UniHaven] Reservation Cancelled",
                message=f"Dear CEDARS,\n\nStudent {student_name} has cancelled their reservation for '{accommodation.title}'.\nNo further action is required.\n\nRegards,\nUniHaven System",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[specialist_email],
            )
            serializer = AccommodationDetailSerializer(accommodation)
            return Response({
                'success': True,
                'message': f'Reservation for accommodation "{accommodation.title}" has been canceled.',
                'UserID': user_id,
                'accommodation': serializer.data
            })
        except Accommodation.DoesNotExist:
            return Response({'success': False, 'message': 'Accommodation not found.'}, 
                            status=status.HTTP_404_NOT_FOUND)

class RatingView(GenericAPIView):
    """
    为住宿评分的视图。
    学生使用的功能，不需要API密钥认证。
    """
    serializer_class = RatingSerializer  # 使用现有的RatingSerializer

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
@renderer_classes([TemplateHTMLRenderer])
def api_key_management(request):
    """ATest whether the API key is valid"""
    return Response(template_name='accommodation/api_key_management.html')

@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
def manage_accommodations(request):
    """The dormitory administrator page view is used to delete accommodation"""
    return Response(template_name='accommodation/manage_accommodation.html')

@api_view(['GET'])
@authentication_classes([UniversityAPIKeyAuthentication])
def test_api_key(request):
    """Test whether the API key is valid"""
    university = request.user
    return Response({
        "success": True,
        "message": "API密钥有效",
        "university": university.name,
        "code": university.code
    })