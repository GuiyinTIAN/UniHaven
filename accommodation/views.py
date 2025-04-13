import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Accommodation
from .forms import AccommodationForm
from django.utils.dateparse import parse_date
from django.db.models import Q, F, Func, FloatField, ExpressionWrapper
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.mail import send_mail
import math

HKU_LATITUDE = 22.28143  # 香港大学的纬度
HKU_LONGITUDE = 114.14006  # 香港大学的经度

def index(request):
    """首页视图函数"""
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({"message": "Welcome to UniHaven!"})
    return render(request, 'accommodation/index.html')

def lookup_address(request):
    """调用香港政府 API 查找地址"""
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

                # 返回地址信息
                return JsonResponse({
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
                }, json_dumps_params={'ensure_ascii': False})
            else:
                return JsonResponse({"error": "No results found"}, status=404)
        except ValueError:
            return JsonResponse({"error": "Invalid JSON response from API"}, status=500)

    except requests.HTTPError as e:
        return JsonResponse({"error": f"HTTP Error: {e.response.status_code}"}, status=e.response.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def add_accommodation(request):
    """添加住宿信息"""
    if request.method == "POST":
        if request.headers.get('Content-Type') == 'application/json':
            # 解析 JSON 数据
            import json
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "message": "Invalid JSON data."}, status=400)
        else:
            # 解析表单数据
            data = request.POST

        form = AccommodationForm(data)
        if form.is_valid():
            accommodation = form.save(commit=False)
            address = form.cleaned_data['address']

            # 调用地址查找 API
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

                # 默认返回 JSON 响应
                return JsonResponse({"success": True, "message": "Accommodation added successfully!"})
            except requests.RequestException as e:
                form.add_error(None, f"Error fetching geolocation: {str(e)}")
        else:
            # 返回错误响应
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    else:
        form = AccommodationForm()

    # 默认返回 HTML 页面
    return render(request, 'accommodation/add_accommodation.html', {'form': form})


def list_accommodation(request):
    """列出所有住宿信息，并支持根据距离筛选"""
    accommodations = Accommodation.objects.all()
    building_name = request.GET.get("building_name", "")
    accommodation_type = request.GET.get("type", "")
    region = request.GET.get("region", "")
    available_from = request.GET.get("available_from", "")
    available_to = request.GET.get("available_to", "")
    min_beds = request.GET.get("min_beds", "")
    min_bedrooms = request.GET.get("min_bedrooms", "")
    max_price = request.GET.get("max_price", "")
    max_distance = request.GET.get("distance", "")  # 最大距离（公里）
    order_by_distance = request.GET.get("order_by_distance", "false").lower() == "true"

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

    # 根据距离计算并筛选
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
            ) * 6371,  # 地球半径（公里）
            output_field=FloatField(),
        )
    )

    # 根据最大距离筛选
    if max_distance:
        try:
            max_distance = float(max_distance)
            accommodations = accommodations.filter(distance__lte=max_distance)
        except ValueError:
            pass

    # 按距离排序
    if order_by_distance:
        accommodations = accommodations.order_by('distance')

    # 返回 JSON 或 HTML 响应
    if request.headers.get('Accept') == 'application/json':
        accommodations_data = list(accommodations.values(
            'id', 'title', 'description', 'type', 'price', 'beds', 'bedrooms',
            'available_from', 'available_to', 'region', 'distance', 'building_name',
        ))
        return JsonResponse({'accommodations': accommodations_data})

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


def search_accommodation(request):
    """搜索住宿信息"""
    if request.GET and any(request.GET.values()):
        # 如果请求头为 JSON，直接返回住宿信息
        if request.headers.get('Accept') == 'application/json':
            return list_accommodation(request)
        # 否则重定向到列表页面
        query_params = request.GET.urlencode()
        return redirect(f"{reverse('list_accommodation')}?{query_params}")
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({"message": "Use GET with query parameters to search accommodations."})
    return render(request, 'accommodation/search_results.html')


def accommodation_detail(request, pk):
    """查看住宿详情"""
    try:
        accommodation = Accommodation.objects.get(pk=pk)
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                "id": accommodation.id,
                "title": accommodation.title,
                "description": accommodation.description,
                "type": accommodation.type,
                "price": accommodation.price,
                "beds": accommodation.beds,
                "bedrooms": accommodation.bedrooms,
                "available_from": accommodation.available_from,
                "available_to": accommodation.available_to,
                "region": accommodation.region,
                "reserved": accommodation.reserved,
                "formatted_address": accommodation.formatted_address(),
            })
        return render(request, 'accommodation/accommodation_detail.html', {'accommodation': accommodation})
    except Accommodation.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Accommodation not found.'}, status=404)

@csrf_exempt
def reserve_accommodation(request, accommodation_id):
    """预订住宿"""
    if request.method == 'POST':
        user_id = request.COOKIES.get('user_identifier')  # 从 Cookie 获取用户 ID

        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID is required.'}, status=400)

        try:
            accommodation = Accommodation.objects.get(id=accommodation_id)

            if accommodation.reserved:
                return JsonResponse({
                    'success': False,
                    'message': f'Accommodation "{accommodation.title}" is already reserved.'
                }, status=400)

            # 预订住宿
            accommodation.reserved = True
            accommodation.userID = user_id  # 关联用户
            accommodation.save()

            # Confirmation Email to Student
            student_email = f"{user_id}@example.com"  
            send_mail(
                subject="Reservation Confirmed - UniHaven",
                message=f"Hi {user_id},\n\nYour reservation for '{accommodation.title}' is confirmed.\nThank you!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
            )

            # Notify CEDARS Specialist 
            specialist_email = "cedars@hku.hk"  
            send_mail(
                subject="[UniHaven] New Reservation Alert",
                message=f"Dear CEDARS,\n\nStudent {user_id} has reserved the accommodation: '{accommodation.title}'.\nPlease follow up for contract processing.\n\nRegards,\nUniHaven System",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[specialist_email],
            )

            return JsonResponse({
                'success': True,
                'message': f'Accommodation "{accommodation.title}" has been reserved.',
                'UserID': user_id,
                'accommodation': {
                    'id': accommodation.id,
                    'reserved': accommodation.reserved
                }
            })
        except Accommodation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Accommodation not found.'}, status=404)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

@csrf_exempt
def cancel_reservation(request, accommodation_id):
    """取消预订"""
    if request.method == 'POST':
        user_id = request.COOKIES.get('user_identifier')  # 从 Cookie 获取用户 ID

        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID is required.'}, status=400)

        try:
            accommodation = Accommodation.objects.get(id=accommodation_id)

            if not accommodation.reserved:
                return JsonResponse({
                    'success': False,
                    'message': f'Accommodation "{accommodation.title}" is not reserved.'
                }, status=400)

            if str(accommodation.userID) != user_id:  # 检查用户 ID 是否匹配
                return JsonResponse({
                    'success': False,
                    'message': 'You are not authorized to cancel this reservation.'
                }, status=403)

            # Cancel the reservation
            accommodation.reserved = False
            accommodation.userID = ""  # Reset the userID
            accommodation.save()


            # Email to Student
            student_email = f"{user_id}@example.com"
            send_mail(
                subject="Reservation Cancelled - UniHaven",
                message=f"Hi {user_id},\n\nYour reservation for '{accommodation.title}' has been cancelled.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
            )

            # Notify CEDARS Specialist about cancellation
            specialist_email = "cedars@hku.hk"  
            send_mail(
                subject="[UniHaven] Reservation Cancelled",
                message=f"Dear CEDARS,\n\nStudent {user_id} has cancelled their reservation for '{accommodation.title}'.\nNo further action is required.\n\nRegards,\nUniHaven System",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[specialist_email],
            )

            # 取消预订
            accommodation.reserved = False
            accommodation.userID = ""  # 重置用户 ID
            accommodation.save()

            return JsonResponse({
                'success': True,
                'message': f'Reservation for accommodation "{accommodation.title}" has been canceled.',
                'UserID': user_id,
                'accommodation': {
                    'id': accommodation.id,
                    'reserved': accommodation.reserved
                }
            })
        except Accommodation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Accommodation not found.'}, status=404)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)