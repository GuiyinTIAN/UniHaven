import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Accommodation
from .forms import AccommodationForm
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.urls import reverse
from django.db.models import F, Func, FloatField, ExpressionWrapper
import math
HKU_latitude = 22.28143
HKU_longitude = 114.14006
def index(request):
    """首页视图函数"""
    return render(request, 'accommodation/index.html')

# test API
def lookup_address(request):
    address = request.GET.get("address", "")
    if not address:
        return JsonResponse({"error": "Address parameter is required"}, status=400)
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

                # English address information
                eng_building_name = eng_address.get("BuildingName", "")
                eng_estate_name = eng_address.get("EngEstate", {}).get("EstateName", "")
                eng_street_name = eng_address.get("EngStreet", {}).get("StreetName", "")
                eng_building_no = eng_address.get("EngStreet", {}).get("BuildingNoFrom", "")
                eng_district = eng_address.get("EngDistrict", {}).get("DcDistrict", "")
                eng_region = eng_address.get("Region", "")

                # Chinese address information
                chi_building_name = chi_address.get("BuildingName", "")
                chi_estate_name = chi_address.get("ChiEstate", {}).get("EstateName", "")
                chi_street_name = chi_address.get("ChiStreet", {}).get("StreetName", "")
                chi_building_no = chi_address.get("ChiStreet", {}).get("BuildingNoFrom", "")
                chi_district = chi_address.get("ChiDistrict", {}).get("DcDistrict", "")
                chi_region = chi_address.get("Region", "")

                # Geospatial information
                latitude = geospatial_info.get("Latitude", None)
                longitude = geospatial_info.get("Longitude", None)
                northing = geospatial_info.get("Northing", None)
                easting = geospatial_info.get("Easting", None)

                return JsonResponse({
                    "EnglishAddress": {
                        "BuildingName": eng_building_name,
                        "EstateName": eng_estate_name,
                        "StreetName": eng_street_name,
                        "BuildingNo": eng_building_no,
                        "District": eng_district,
                        "Region": eng_region
                    },
                    "ChineseAddress": {
                        "BuildingName": chi_building_name,
                        "EstateName": chi_estate_name,
                        "StreetName": chi_street_name,
                        "BuildingNo": chi_building_no,
                        "District": chi_district,
                        "Region": chi_region
                    },
                    "GeospatialInformation": {
                        "Latitude": latitude,
                        "Longitude": longitude,
                        "Northing": northing,
                        "Easting": easting,
                        "GeoAddress": geo_address
                    }
                }, json_dumps_params={'ensure_ascii': False})
            else:
                return JsonResponse({"error": "No results found"}, status=404)
        except ValueError:
           # debugging
            print("Response Text (Debug):", response.text)
            return JsonResponse({"error": "Invalid JSON response from API"}, status=500)

    except requests.HTTPError as e:
        # debugging
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return JsonResponse({"error": f"HTTP Error: {e.response.status_code}"}, status=e.response.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)



def add_accommodation(request):
    if request.method == "POST":
        form = AccommodationForm(request.POST)
        if form.is_valid():
            accommodation = form.save(commit=False)
            address = form.cleaned_data['address']

            api_url = f"https://www.als.gov.hk/lookup?q={address}&n=1"
            headers = {"Accept": "application/json"}
            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                print("API 响应:", response.text)
                data = response.json()

                # 从 API 响应中提取地理信息
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
                return redirect('add_accommodation')
            except requests.RequestException as e:
                form.add_error(None, f"Error fetching geolocation: {str(e)}")
    else:
        form = AccommodationForm()

    return render(request, 'accommodation/add_accommodation.html', {'form': form})


def list_accommodation(request):
    accommodations = Accommodation.objects.all()
    accommodation_type = request.GET.get("type", "")
    region = request.GET.get("region", "")
    available_from = request.GET.get("available_from", "")
    available_to = request.GET.get("available_to", "")
    min_beds = request.GET.get("min_beds", "")
    min_bedrooms = request.GET.get("min_bedrooms", "")
    max_price = request.GET.get("max_price", "")
    max_distance = request.GET.get("distance", "")

    # 过滤房源类型
    if accommodation_type:
        accommodations = accommodations.filter(type=accommodation_type)

    # 过滤地区
    if region:
        accommodations = accommodations.filter(region=region)

    # 过滤日期范围
    if available_from and available_to:
        try:
            available_from = parse_date(available_from)
            available_to = parse_date(available_to)
            if available_from and available_to:
                accommodations = accommodations.filter(
                    Q(available_from__lte=available_from) & Q(available_to__gte=available_to)
                )
        except ValueError:
            print("Invalid date format")  # 调试信息

    # 过滤床位数
    if min_beds:
        accommodations = accommodations.filter(beds__gte=min_beds)

    # 过滤卧室数
    if min_bedrooms:
        accommodations = accommodations.filter(bedrooms__gte=min_bedrooms)

    # 过滤价格
    if max_price:
        accommodations = accommodations.filter(price__lte=max_price)
    
        # Calculate distance dynamically and filter
    if max_distance:
        max_distance = float(max_distance)

        # Add distance annotation using the equirectangular approximation formula
        accommodations = accommodations.annotate(
            distance=ExpressionWrapper(
                Func(
                    Func(
                        (F('longitude') - HKU_longitude) * math.pi / 180 *
                        Func((F('latitude') + HKU_latitude) / 2 * math.pi / 180, function='COS'),
                        function='POW',
                        template="%(function)s(%(expressions)s, 2)"
                    ) +
                    Func(
                        (F('latitude') - HKU_latitude) * math.pi / 180,
                        function='POW',
                        template="%(function)s(%(expressions)s, 2)"
                    ),
                    function='SQRT',
                ) * 6371,  # Earth's radius in kilometers
                output_field=FloatField(),
            )
        ).filter(distance__lte=max_distance)

    

    return render(request, 'accommodation/accommodation_list.html', {
        'accommodations': accommodations,
        'accommodation_type': accommodation_type,
        'region': region,
        'available_from': available_from,
        'available_to': available_to,
        'min_beds': min_beds,
        'min_bedrooms': min_bedrooms,
        'max_price': max_price,
        'max_distance': max_distance,
    })


def search_accommodation(request):
    if request.GET and any(request.GET.values()):
        query_params = request.GET.urlencode()
        return redirect(f"{reverse('list_accommodation')}?{query_params}")
    else:
        return render(request, 'accommodation/search_results.html')


def accommodation_detail(request, pk):
    accommodation = Accommodation.objects.get(pk=pk)
    return render(request, 'accommodation/accommodation_detail.html', {'accommodation': accommodation})


# Equirectangular approximation formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2 * math.pi / 180)
    y = (lat2 - lat1)
    distance = math.sqrt(x**2 + y**2) * R
    return distance


