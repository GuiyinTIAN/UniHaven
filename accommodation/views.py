import requests
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.utils.dateparse import parse_date
from django.db.models import Q, F, Func, FloatField, ExpressionWrapper
from django.urls import reverse
from django.core.mail import send_mail

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, renderer_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from .models import Accommodation
from .forms import AccommodationForm
from .serializers import (
    AccommodationSerializer, 
    AccommodationDetailSerializer,
    AccommodationListSerializer
)

# Geographic coordinates of The University of Hong Kong
HKU_LATITUDE = 22.28143
HKU_LONGITUDE = 114.14006

@api_view(['GET'])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def index(request):
    """Home page view function"""
    if request.accepted_renderer.format == 'json':
        return Response({"message": "Welcome to UniHaven!"})
    return Response({}, template_name='accommodation/index.html')

@api_view(['GET'])
def lookup_address(request):
    """Call Hong Kong government API to look up addresses"""
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
                        "Region": eng_address.get("Region", "")
                    },
                    "ChineseAddress": {
                        "BuildingName": chi_address.get("BuildingName", ""),
                        "EstateName": chi_address.get("ChiEstate", {}).get("EstateName", ""),
                        "StreetName": chi_address.get("ChiStreet", {}).get("StreetName", ""),
                        "BuildingNo": chi_address.get("ChiStreet", {}).get("BuildingNoFrom", ""),
                        "District": chi_address.get("ChiDistrict", {}).get("DcDistrict", ""),
                        "Region": chi_address.get("Region", "")
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

@api_view(['GET', 'POST'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def add_accommodation(request):
    """Add new accommodation information"""
    if request.method == "POST":
        serializer = AccommodationSerializer(data=request.data)
        if serializer.is_valid():
            accommodation = Accommodation()
            
            fields = ['title', 'description', 'type', 'price', 'beds', 
                     'bedrooms', 'available_from', 'available_to',
                     'contact_phone', 'contact_email']
            
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

                accommodation.save()
                return Response(
                    {"success": True, "message": "Accommodation added successfully!"}, 
                    status=status.HTTP_201_CREATED
                )
            except requests.RequestException as e:
                return Response(
                    {"success": False, "message": f"Error fetching geolocation: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {"success": False, "errors": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        form = AccommodationForm()
        return render(request, 'accommodation/add_accommodation.html', {'form': form})

@api_view(['GET'])
def list_accommodation(request):
    """List all accommodations with optional distance-based filtering"""
    accommodations = Accommodation.objects.all()
    
    building_name = request.query_params.get("building_name", "")
    accommodation_type = request.query_params.get("type", "")
    region = request.query_params.get("region", "")
    available_from = request.query_params.get("available_from", "")
    available_to = request.query_params.get("available_to", "")
    min_beds = request.query_params.get("min_beds", "")
    min_bedrooms = request.query_params.get("min_bedrooms", "")
    max_price = request.query_params.get("max_price", "")
    max_distance = request.query_params.get("distance", "")
    order_by_distance = request.query_params.get("order_by_distance", "false").lower() == "true"

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
                    (F('longitude') - HKU_LONGITUDE) * math.pi / 180 *
                    Func((F('latitude') + HKU_LATITUDE) / 2 * math.pi / 180, function='COS'),
                    function='POW',
                    template="%(function)s(%(expressions)s, 2)"
                ) +
                Func(
                    (F('latitude') - HKU_LATITUDE) * math.pi / 180,
                    function='POW',
                    template="%(function)s(%(expressions)s, 2)"
                ),
                function='SQRT',
            ) * 6371,  # Earth radius (km)
            output_field=FloatField(),
        )
    )

    if max_distance:
        try:
            max_distance = float(max_distance)
            accommodations = accommodations.filter(distance__lte=max_distance)
        except ValueError:
            pass

    if order_by_distance:
        accommodations = accommodations.order_by('distance')

    if request.headers.get('Accept') == 'application/json':
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
        'order_by_distance': order_by_distance,
    })

@api_view(['GET'])
def search_accommodation(request):
    """Search for accommodations with filters"""
    if request.GET and any(request.GET.values()):
        # 始终使用重定向而不是直接调用函数，避免请求对象类型错误
        query_params = request.GET.urlencode()
        if request.headers.get('Accept') == 'application/json':
            # 添加一个标记参数以便接收端知道这是一个JSON请求
            return redirect(f"{reverse('list_accommodation')}?{query_params}&format=json")
        return redirect(f"{reverse('list_accommodation')}?{query_params}")
    
    if request.headers.get('Accept') == 'application/json':
        return Response({"message": "Use GET with query parameters to search accommodations."})
    
    return render(request, 'accommodation/search_results.html')

@api_view(['GET'])
def accommodation_detail(request, pk):
    """View accommodation details"""
    try:
        accommodation = get_object_or_404(Accommodation, pk=pk)
        
        if request.headers.get('Accept') == 'application/json':
            serializer = AccommodationDetailSerializer(accommodation)
            return Response(serializer.data)
        
        return render(request, 'accommodation/accommodation_detail.html', {'accommodation': accommodation})
    
    except Accommodation.DoesNotExist:
        return Response({'error': 'Accommodation not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def reserve_accommodation(request):
    """Reserve an accommodation using query parameter id"""
    accommodation_id = request.query_params.get('id')
    if not accommodation_id:
        return Response({'success': False, 'message': 'Accommodation ID is required'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    user_id = request.COOKIES.get('user_identifier')
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

        accommodation.reserved = True
        accommodation.userID = user_id
        accommodation.save()

        student_email = f"{user_id}@example.com"  
        send_mail(
            subject="Reservation Confirmed - UniHaven",
            message=f"Hi {user_id},\n\nYour reservation for '{accommodation.title}' is confirmed.\nThank you!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
        )

        specialist_email = "cedars@hku.hk"  
        send_mail(
            subject="[UniHaven] New Reservation Alert",
            message=f"Dear CEDARS,\n\nStudent {user_id} has reserved the accommodation: '{accommodation.title}'.\nPlease follow up for contract processing.\n\nRegards,\nUniHaven System",
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

@api_view(['POST'])
def cancel_reservation(request):
    """Cancel an accommodation reservation using query parameter id"""
    accommodation_id = request.query_params.get('id')
    if not accommodation_id:
        return Response({'success': False, 'message': 'Accommodation ID is required'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    user_id = request.COOKIES.get('user_identifier')
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
                'message': f'You are not authorized to cancel this reservation. The accommodation can only be canceld by [{accommodation.userID}].'
            }, status=status.HTTP_403_FORBIDDEN)

        accommodation.reserved = False
        accommodation.userID = ""
        accommodation.save()

        student_email = f"{user_id}@example.com"
        send_mail(
            subject="Reservation Cancelled - UniHaven",
            message=f"Hi {user_id},\n\nYour reservation for '{accommodation.title}' has been cancelled.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
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