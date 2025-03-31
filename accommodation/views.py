import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Accommodation
from .forms import AccommodationForm
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.urls import reverse

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
            # debugging
            print("Response Text (Debug):", response.text)
            return JsonResponse({"error": "Invalid JSON response from API"}, status=500)

    except requests.HTTPError as e:
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
            pass

    # 过滤床位数
    if min_beds:
        accommodations = accommodations.filter(beds__gte=min_beds)

    # 过滤卧室数
    if min_bedrooms:
        accommodations = accommodations.filter(bedrooms__gte=min_bedrooms)

    # 过滤价格
    if max_price:
        accommodations = accommodations.filter(price__lte=max_price)

    return render(request, 'accommodation/accommodation_list.html', {
        'accommodations': accommodations,
        'accommodation_type': accommodation_type,
        'region': region,
        'available_from': available_from,
        'available_to': available_to,
        'min_beds': min_beds,
        'min_bedrooms': min_bedrooms,
        'max_price': max_price,
    })

def search_accommodation(request):
    if request.GET and any(request.GET.values()):
        query_params = request.GET.urlencode()
        return redirect(f"{reverse('list_accommodation')}?{query_params}")
    else:
        return render(request, 'accommodation/search_results.html')


def accommodation_detail(request, pk):
    # Get the accommodation object based on the primary key
    accommodation = Accommodation.objects.get(pk=pk)
    
    # If the form is submitted
    if request.method == 'POST':
        form = AccommodationForm(request.POST, instance=accommodation)
        
        if form.is_valid():
            form.save()  # Save the form data to update the reservation status
            return redirect('accommodation_list')  # Redirect after saving
    else:
        form = AccommodationForm(instance=accommodation)

    return render(request, 'accommodation/accommodation_detail.html', {
        'accommodation': accommodation,
        'form': form
    })

def reserve_accommodation(request, accommodation_id):
    if request.method == 'POST':
        user_id = request.COOKIES.get('user_identifier')  # Retrieve the userID from cookies

        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID is required.'}, status=400)

        try:
            accommodation = Accommodation.objects.get(id=accommodation_id)

            if accommodation.reserved:
                return JsonResponse({
                    'success': False,
                    'message': f'Accommodation "{accommodation.title}" is already reserved.'
                }, status=400)

            # Reserve the accommodation
            accommodation.reserved = True
            accommodation.userID = user_id  # Associate the reservation with the user
            accommodation.save()

            return JsonResponse({
                'success': True,
                'message': f'Accommodation "{accommodation.title}" has been reserved.',
                'accommodation': {
                    'id': accommodation.id,
                    'reserved': accommodation.reserved
                }
            })
        except Accommodation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Accommodation not found.'}, status=404)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)
    
def cancel_reservation(request, accommodation_id):
    if request.method == 'POST':
        user_id = request.COOKIES.get('user_identifier')  # Retrieve the userID from cookies

        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID is required.'}, status=400)

        try:
            accommodation = Accommodation.objects.get(id=accommodation_id)

            if not accommodation.reserved:
                return JsonResponse({
                    'success': False,
                    'message': f'Accommodation "{accommodation.title}" is not reserved.'
                }, status=400)

            if str(accommodation.userID) != user_id:  # Check if the userID matches
                return JsonResponse({
                    'success': False,
                    'message': 'You are not authorized to cancel this reservation.'
                }, status=403)

            # Cancel the reservation
            accommodation.reserved = False
            accommodation.userID = ""  # Reset the userID
            accommodation.save()

            return JsonResponse({
                'success': True,
                'message': f'Reservation for accommodation "{accommodation.title}" has been canceled.',
                'accommodation': {
                    'id': accommodation.id,
                    'reserved': accommodation.reserved
                }
            })
        except Accommodation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Accommodation not found.'}, status=404)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)