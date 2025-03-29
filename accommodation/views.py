import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Accommodation
from .forms import AccommodationForm

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

def accommodation_list(request):
    accommodations = Accommodation.objects.all()
    return render(request, 'accommodation/accommodation_list.html', {'accommodations': accommodations})
