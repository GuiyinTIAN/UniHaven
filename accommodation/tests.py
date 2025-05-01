from django.test import TestCase

# Create your tests here.
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.timezone import now
from accommodation.models import Accommodation, University, AccommodationRating, AccommodationUniversity, UniversityAPIKey, ReservationPeriod
import datetime
import uuid


class AccommodationAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # 创建测试大学
        cls.hku, _ = University.objects.get_or_create(
            code="HKU",
            defaults={
                "name": "The University of Hong Kong",
                "specialist_email": "cedarsg@hku.hk"
            }
        )
        cls.hkust, _ = University.objects.get_or_create(
            code="HKUST",
            defaults={
                "name": "The Hong Kong University of Science and Technology",
                "specialist_email": "housing@ust.hk"
            }
        )
        cls.cuhk, _ = University.objects.get_or_create(
            code="CUHK",
            defaults={
                "name": "The Chinese University of Hong Kong",
                "specialist_email": "housing@cuhk.edu.hk"
            }
        )
        cls.hku_api_key = UniversityAPIKey.objects.create(
            university=cls.hku,
            key="e6861bfe8eaa4994a8633222a136c78c",  # HKU 的固定密钥
            is_active=True,
            last_used=now()
        )
        cls.cuhk_api_key = UniversityAPIKey.objects.create(
            university=cls.cuhk,
            key="586385e5a18c46e3a3a5c9162599320f",  # CUHK 的固定密钥
            is_active=True,
            last_used=now()
        )
        cls.hkust_api_key = UniversityAPIKey.objects.create(
            university=cls.hkust,
            key="96a847fd519845099624b757d22c7424",  # HKUST 的固定密钥
            is_active=True,
            last_used=now()
        )

        # 创建测试住宿
        cls.accommodation_1 = Accommodation.objects.create(
            title="Luxury Apartment",
            type="APARTMENT",
            price=5000.00,
            beds=2,
            bedrooms=1,
            available_from="2025-05-01",
            available_to="2025-10-01",
            reserved=False,
            building_name="Princeton Tower",
            room_number="A1001",
            flat_number="A",
            floor_number="10",
            latitude=22.3964,
            longitude=114.1099,
        )
        
        cls.accommodation_2 = Accommodation.objects.create(
            title="Budget Apartment",
            type="APARTMENT",
            price=2000.00,
            beds=1,
            bedrooms=1,
            available_from="2025-06-01",
            available_to="2025-12-01",
            reserved=False,
            building_name="Novum West",
            room_number="B2002",
            flat_number="B",
            floor_number="20",
            latitude=22.28554,
            longitude=114.13653,
        )
        
        cls.accommodation_3 = Accommodation.objects.create(
            title="Luxury Villa",
            type="House",
            price=8000.00,
            beds=4,
            bedrooms=3,
            available_from="2025-07-01",
            available_to="2025-09-01",
            reserved=False,
            building_name="kennedy Town",
            room_number="C3003",
            flat_number="C",
            floor_number="30",
            latitude=22.28367,
            longitude=114.12809,
        )
        # 将住宿与大学关联
        cls.accommodation_1.affiliated_universities.add(cls.hku, cls.hkust, cls.cuhk)
        cls.accommodation_2.affiliated_universities.add(cls.hku, cls.hkust)
        cls.accommodation_3.affiliated_universities.add(cls.cuhk)

    def test_home_page_json(self):
        url = reverse('index')
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Welcome to UniHaven!")

    def test_accommodation_detail_api(self):
        """测试 Accommodation Detail API"""
        # 获取测试住宿的详细信息的 URL
        url = f'/api/accommodation_detail/{self.accommodation_1.id}/'

        # 发送 GET 请求
        response = self.client.get(url, {"format":'json'})

        # 检查状态码是否为 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 检查返回的数据是否正确
        expected_data = {
            'id': self.accommodation_1.id,
            'title': self.accommodation_1.title,
            'description': self.accommodation_1.description,  # 添加 description 字段
            'type': self.accommodation_1.type,
            'price': f"{self.accommodation_1.price:.2f}",  # 确保价格格式为字符串，带两位小数
            'beds': self.accommodation_1.beds,
            'bedrooms': self.accommodation_1.bedrooms,
            'available_from': str(self.accommodation_1.available_from),
            'available_to': str(self.accommodation_1.available_to),
            'region': self.accommodation_1.region,  # 添加 region 字段
            'reserved': self.accommodation_1.reserved,
            'formatted_address': self.accommodation_1.formatted_address(),  # 添加 formatted_address 字段
            'building_name': self.accommodation_1.building_name,
            'room_number': self.accommodation_1.room_number,
            'floor_number': self.accommodation_1.floor_number,
            'flat_number': self.accommodation_1.flat_number,
            'contact_name': self.accommodation_1.contact_name,  # 添加 contact_name 字段
            'contact_phone': self.accommodation_1.contact_phone,  # 添加 contact_phone 字段
            'contact_email': self.accommodation_1.contact_email,  # 添加 contact_email 字段
            'rating': self.accommodation_1.rating,  # 添加 rating 字段
            'rating_count': self.accommodation_1.rating_count,  # 添加 rating_count 字段
            'rating_sum': self.accommodation_1.rating_sum,  # 添加 rating_sum 字段
            'affiliated_university_codes': [  # 修改为仅包含大学代码
                self.hku.code,
                self.hkust.code,
                self.cuhk.code
            ],
        }
        self.assertEqual(response.json(), expected_data)
    def test_add_accommodation_1(self):
        """测试 Add Accommodation API"""
        # URL
        url = '/api/add-accommodation/?api_key=586385e5a18c46e3a3a5c9162599320f'

        # 请求数据
        data = {
            "title": "test case",
            "description": "1",
            "type": "APARTMENT",
            "price": "3100.00",
            "beds": 1,  
            "bedrooms": 2,  
            "available_from": "2025-04-28",
            "available_to": "2025-05-30",
            "building_name": "top",
            "room_number": "1001",
            "floor_number": "10",
            "flat_number": "A",
            "contact_phone": "90909090",
            "contact_email": "user@example.com"
        }

        # 发送 POST 请求
        response = self.client.post(url, data, format='json')

        # 检查状态码是否为 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_id = response.data['id']
        # 检查数据库是否已创建对应的 Accommodation
        accommodation = Accommodation.objects.get(id=new_id)
        self.assertEqual(accommodation.description, data['description'])
        self.assertEqual(accommodation.type, data['type'])
        self.assertEqual(accommodation.price, float(data['price']))
        self.assertEqual(accommodation.title, data['title'])
        self.assertEqual(accommodation.beds, data['beds'])
        self.assertEqual(accommodation.bedrooms, data['bedrooms'])
        self.assertEqual(str(accommodation.available_from), data['available_from'])
        self.assertEqual(str(accommodation.available_to), data['available_to'])
        # self.assertEqual(accommodation.building_name, data['building_name'])
        self.assertEqual(accommodation.room_number, data['room_number'])
        self.assertEqual(accommodation.floor_number, data['floor_number'])
        self.assertEqual(accommodation.flat_number, data['flat_number'])
        self.assertEqual(accommodation.contact_phone, data['contact_phone'])
        self.assertEqual(accommodation.contact_email, data['contact_email'])
        # 测试不同的大学能否添加同样的宿舍
        url = f'/api/add-accommodation/?api_key={self.hku_api_key.key}'
        data = {
            "title": "test case ",
            "description": "1",
            "type": "APARTMENT",
            "price": "3100.00",
            "beds": 1,  
            "bedrooms": 2,  
            "available_from": "2025-04-28",
            "available_to": "2025-05-30",
            "address": "top",
            "room_number": "1001",
            "floor_number": "10",
            "flat_number": "A",
            "contact_phone": "90909090",
            "contact_email": "user@example.com"
        }

        # 发送 POST 请求
        response = self.client.post(url, data, format='json')

        # 检查状态码是否为 400_BAD_REQUEST
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # test list_accommodation API
    
    def test_list_accommodation_with_filters(self):
        """测试带过滤条件的住宿查询"""
        url = '/api/list-accommodation/'
        params = {
            "type": "APARTMENT",  # 只查询 HOUSE 类型
            "format": "json"
        }
        response = self.client.get(url, params)
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["accommodations"]), 2) # 检查返回的住宿数量
        # 检查返回的住宿数量

    def test_list_accommodation_no_filters(self):
        """测试无过滤条件时返回所有住宿"""
        url = '/api/list-accommodation/'
        params = {
            "format": "json"
        }
        response = self.client.get(url, params)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 检查返回的住宿数量是否为数据库中所有住宿的数量
        self.assertEqual(len(response.json()["accommodations"]), Accommodation.objects.count())
    
    def test_list_accommodation_user_id_filter(self):
        """测试根据用户 ID 过滤住宿"""
        url = '/api/list-accommodation/'
        params = {
            "user_id": "HKUST_123", 
            "format": "json"
        }
        response = self.client.get(url, params)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 检查返回的住宿数量是否正确
        accommodations = response.json()["accommodations"]
        # 验证返回的住宿是否与用户的大学相关联
        for accommodation in accommodations:
            self.assertIn(accommodation["id"], [self.accommodation_1.id, self.accommodation_2.id])

    def test_list_accommodation_order_by_price(self):
        """测试根据价格升序排序"""
        url = '/api/list-accommodation/'
        params = {
            "order_by": "price_asc",  # 按价格升序排序
            "format": "json"
        }
        response = self.client.get(url, params)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 检查返回的住宿是否按价格升序排序
        accommodations = response.json()["accommodations"]
        prices = [float(accommodation["price"]) for accommodation in accommodations]
        self.assertEqual(prices, sorted(prices))

    def test_list_accommodation_date_filter(self):
        """测试根据可用日期范围过滤住宿"""
        url = '/api/list-accommodation/'
        params = {
            "available_from": "2025-05-01",
            "available_to": "2025-06-01",
            "format": "json"
        }
        response = self.client.get(url, params)
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        # 检查返回的住宿是否都在指定日期范围内
        accommodations = response.json()["accommodations"]
        self.assertTrue(all(
            accommodation["available_from"] <= "2025-05-01" and accommodation["available_to"] >= "2025-06-01"
            for accommodation in accommodations
        ))
    def test_reserve_accommodation_success_post(self):
        """测试通过 POST 请求成功预订宿舍"""
        # 确保宿舍未被预订
        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123&contact_number=98765432"  # 添加contact_number
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 检查数据库中住宿的状态
        self.accommodation_1.refresh_from_db()
        
        # 验证是否已创建ReservationPeriod
        reservation = ReservationPeriod.objects.get(accommodation=self.accommodation_1, user_id="HKU_123")
        self.assertEqual(reservation.user_id, "HKU_123")
        self.assertEqual(reservation.contact_number, "98765432")

        """测试不能预定已经预定的宿舍"""
        query_params = f"id={self.accommodation_1.id}&User%20ID=CUHK_123"
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reserve_accommodation_only_for_specified_university_post(self):
        """测试只能为指定大学预订宿舍"""
        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_3.id}&User%20ID=HKU_123&contact_number=98765432"
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    def test_cancel_reservation_success(self):
        """测试成功取消预订"""
        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123&contact_number=98765432"
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求预订
        
        # 检查预订状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('cancel_reservation')  # 动态生成取消预订的 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123"  # 添加必要的查询参数
        full_url = f"{url}?{query_params}"

        response = self.client.put(full_url)  # 改为发送 PUT 请求

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 检查ReservationPeriod是否已被删除
        self.assertFalse(ReservationPeriod.objects.filter(accommodation=self.accommodation_1, user_id="HKU_123").exists())
    
    def test_cancel_reservation_wrong_user(self):
        """测试用户尝试取消不属于自己的预订"""

        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123&contact_number=98765432"
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求预订
        
        # 检查预订状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('cancel_reservation')  # 动态生成取消预订的 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_456"  # 错误的用户 ID
        full_url = f"{url}?{query_params}"

        response = self.client.put(full_url)  # 改为发送 PUT 请求

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_reservation_not_found(self):
        """测试取消不存在的住宿"""
        url = reverse('cancel_reservation')  # 动态生成取消预订的 URL
        query_params = f"id=9999&User%20ID=HKU_123"  # 不存在的住宿 ID
        full_url = f"{url}?{query_params}"

        response = self.client.put(full_url)  # 改为发送 PUT 请求

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_reservation_not_reserved(self):
        """测试取消未预订的住宿"""
        url = reverse('cancel_reservation')  # 动态生成取消预订的 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123"  # 未预订的住宿
        full_url = f"{url}?{query_params}"

        response = self.client.put(full_url)  # 改为发送 PUT 请求

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_submit_rating_success(self):
        """测试成功提交评分"""
        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123&contact_number=98765432"
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  # 动态生成 URL
        query_params = "?rating=5&userid=HKU_123"
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        # 检查数据库更新
        self.accommodation_1.refresh_from_db()
        self.assertEqual(self.accommodation_1.rating, 5.0)
        self.assertEqual(self.accommodation_1.rating_count, 1)
        self.assertEqual(self.accommodation_1.rating_sum, 5)

    def test_submit_invalid_rating_value(self):
        """测试评分值无效（超出范围）"""
        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123&contact_number=98765432"  # 添加contact_number
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  
        query_params = "?rating=6&userid=HKU_123"  # 无效评分值
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_submit_rating_not_found(self):
        """测试为不存在的住宿提交评分"""
        url = reverse('rate_accommodation', args=[9999])  # 不存在的住宿 ID
        query_params = "?rating=5&userid=HKU_123"
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_submit_rating_already_rated(self):
        """测试用户已经评分的住宿"""
 
        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123&contact_number=98765432"  # 添加contact_number
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  # 动态生成 URL
        query_params = "?rating=5&userid=HKU_123"
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  # 动态生成 URL
        query_params = "?rating=5&userid=HKU_123"
        full_url = f"{url}{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_rating_not_reserved_by_user(self):
        url = reverse('reserve_accommodation')  # 动态生成 URL
        query_params = f"id={self.accommodation_1.id}&User%20ID=HKU_123&contact_number=98765432"  # 添加contact_number
        
        # 构造带查询参数的完整 URL
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)  # 发送 POST 请求
        
        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  # 动态生成 URL
        query_params = "?rating=5&userid=HKU_456"
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_submit_rating_missing_parameters(self):
        """测试缺少参数"""
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  # 动态生成 URL

        # 缺少 rating 参数
        response = self.client.post(f"{url}?userid=HKU_123")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lookup_address_success(self):
        """测试成功查询地址"""
        url = reverse('lookup_address')  
        query_params = "?address=princeton%20tower"
        full_url = f"{url}{query_params}"

        response = self.client.get(full_url)

        # 检查响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data.get('EnglishAddress'))

        # 验证 EnglishAddress 内容
        english_address = data['EnglishAddress']
        self.assertEqual(english_address['BuildingName'], "PRINCETON TOWER")
        self.assertEqual(english_address['StreetName'], "DES VOEUX ROAD WEST")
        self.assertEqual(english_address['BuildingNo'], "88")
        self.assertEqual(english_address['District'], "CENTRAL & WESTERN DISTRICT")
        self.assertEqual(english_address['Region'], "HK")

    def test_remove_university_association(self):
        """测试移除大学与宿舍的关联（多个大学关联时）"""
        api_key = self.hku_api_key.key
        url = f"/api/delete-accommodation/?api_key={api_key}"
        
        response = self.client.post(url, {"id": self.accommodation_1.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(
            response.json()["message"],
            f"Removed {self.hku.name}'s association with accommodation '{self.accommodation_1.title}'. The accommodation is still available to other universities."
        )
        # 验证大学 1 的关联已移除
        self.assertFalse(self.accommodation_1.affiliated_universities.filter(id=self.hku.id).exists())

        # 验证大学 2 的关联仍然存在
        self.assertTrue(self.accommodation_1.affiliated_universities.filter(id=self.hkust.id).exists())
        self.assertTrue(self.accommodation_1.affiliated_universities.filter(id=self.cuhk.id).exists())

    def test_delete_accommodation_when_all_associations_removed(self):
        """
        测试当删除最后一个大学的关联时，宿舍是否会被完全删除。
        """

        # API 请求 URL
        url = f"/api/delete-accommodation/?api_key={self.cuhk_api_key.key}"

        # 发送删除请求
        response = self.client.post(url, {"id": self.accommodation_3.id}, format="json")

        # 验证响应状态码
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证响应内容
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(
            response.json()["message"],
            f"Accommodation '{self.accommodation_3.title}' has been completely deleted."
        )

        # 验证宿舍已从数据库中被删除
        self.assertFalse(Accommodation.objects.filter(id=self.accommodation_3.id).exists())

    def test_accommodation_not_found(self):
        """测试删除不存在的宿舍"""
        url = f"/api/delete-accommodation/?api_key=586385e5a18c46e3a3a5c9162599320f"
        response = self.client.post(url, {"id": 999}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(response.json()["message"], "Accommodation not found.")
    
    def test_distance_calculation(self):
        """测试距离计算"""
        # 定义 API URL 和查询参数
        url = '/api/list-accommodation/'
        params = {
            "price": 2000,
            "type": "APARTMENT",  # 查询 APARTMENT 类型
            "format": "json",
            "distance": "5",  # 设置距离为 5 公里
            "campus": "HKU_main",  # 设置校园为 HKU
        }
        
        # 发起 GET 请求
        response = self.client.get(url, params)
        
        # 检查响应状态码是否为 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 打印 JSON 响应数据用于调试
        response_data = response.json()
        print(response_data)

        
        # 检查返回的住宿列表是否存在
        accommodations = response_data.get("accommodations", [])
        self.assertGreater(len(accommodations), 0, "No accommodations found in the response.")
    

        # 验证第一个住宿的距离是否符合预期
        first_accommodation = accommodations[0]
        print("title:",first_accommodation["title"])
        self.assertIn("distance", first_accommodation, "Distance key is missing in the accommodation data.")
        self.assertAlmostEqual(
            first_accommodation["distance"], 
            0.21358179659004045
        )
            


def generate_unique_code(base="UNI"):
    """Generate a unique code to avoid UNIQUE constraint conflict"""
    return f"{base}_{uuid.uuid4().hex[:6]}"

class UniversityModelTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            code=generate_unique_code("HKU"),
            name="The University of Hong Kong",
            specialist_email="specialist@hku.hk"
        )

    def test_university_str(self):
        self.assertEqual(str(self.university), f"{self.university.name} ({self.university.code})")

class AccommodationModelTest(TestCase):
    def setUp(self):
        self.accommodation = Accommodation.objects.create(
            title="Real Apartment",
            description="A beautiful real-world apartment in Hong Kong.",
            type="APARTMENT",
            beds=2,
            bedrooms=1,
            price=1500.00,
            building_name="利都楼",
            estate_name="康乐园",
            building_no="12",
            street_name="蓝塘道",
            district="湾仔",
            region="香港岛",
            latitude=22.2675,
            longitude=114.1835,
            geo_address="12 Blue Pool Road, Happy Valley, Hong Kong",
        )

    def test_accommodation_basic_fields(self):
        self.assertEqual(self.accommodation.title, "Real Apartment")
        self.assertEqual(self.accommodation.price, 1500.00)

    def test_formatted_address(self):
        expected_address = "利都楼, 康乐园, 12 蓝塘道, 湾仔, 香港岛"
        self.assertEqual(self.accommodation.formatted_address(), expected_address)

    def test_reserved_default_false(self):
        """Test that reserved is False by default when creating Accommodation"""
        self.assertFalse(self.accommodation.reserved)

    def test_save_method_cleans_none_fields(self):
        """Test that save() automatically cleans None fields"""
        acc = Accommodation.objects.create(
            title="Empty Test",
            description="Testing none fields",
            type="HOUSE",
            beds=1,
            bedrooms=1,
            price=800.00,
            latitude=22.3,
            longitude=114.2,
            room_number=None,
            floor_number=None,
            flat_number=None,
            geo_address=None,
        )
        acc.refresh_from_db()
        self.assertEqual(acc.room_number, "")
        self.assertEqual(acc.floor_number, "")
        self.assertEqual(acc.flat_number, "")
        self.assertEqual(acc.geo_address, "")
    


class AccommodationRatingModelTest(TestCase):
    def setUp(self):
        self.accommodation = Accommodation.objects.create(
            title="Sample Place",
            description="Nice and cozy.",
            type="HOUSE",
            beds=3,
            bedrooms=2,
            price=2500.00,
            latitude=22.3,
            longitude=114.2,
        )

    def test_accommodation_rating_str(self):
        rating = AccommodationRating.objects.create(
            accommodation=self.accommodation,
            user_identifier="user123",
            rating=4
        )
        expected_str = f"user123 rated {self.accommodation.title} ({rating.rating})"
        self.assertEqual(str(rating), expected_str)

    def test_rating_value_range(self):
        """Test that rating must be within the range of 0 to 5"""
        invalid_rating1 = AccommodationRating(
            accommodation=self.accommodation,
            user_identifier="user456",
            rating=6
        )
        with self.assertRaises(ValidationError):
            invalid_rating1.full_clean()

        invalid_rating2 = AccommodationRating(
            accommodation=self.accommodation,
            user_identifier="user789",
            rating=-1
        )
        with self.assertRaises(ValidationError):
            invalid_rating2.full_clean()

class AccommodationUniversityModelTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            code=generate_unique_code("CUHK"),
            name="The Chinese University of Hong Kong",
            specialist_email="specialist@cuhk.hk"
        )
        self.accommodation = Accommodation.objects.create(
            title="University Hostel",
            description="On-campus housing.",
            type="HOSTEL",
            beds=1,
            bedrooms=1,
            price=1000.00,
            latitude=22.4,
            longitude=114.2,
        )
        self.accommodation_university = AccommodationUniversity.objects.create(
            accommodation=self.accommodation,
            university=self.university
        )

    def test_accommodation_university_str(self):
        expected_str = f"{self.accommodation.title} - {self.university.code}"
        self.assertEqual(str(self.accommodation_university), expected_str)

    def test_unique_accommodation_university(self):
        """Test that the combination of accommodation and university is unique"""
        with self.assertRaises(Exception):
            AccommodationUniversity.objects.create(
                accommodation=self.accommodation,
                university=self.university
            )

class UniversityAPIKeyModelTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            code=generate_unique_code("HKUST"),
            name="The Hong Kong University of Science and Technology",
            specialist_email="specialist@ust.hk"
        )
        self.api_key = UniversityAPIKey.objects.create(
            university=self.university
        )

    def test_university_api_key_str(self):
        expected_str = f"{self.university.name} API Key"
        self.assertEqual(str(self.api_key), expected_str)

    def test_university_api_key_auto_generate(self):
        """Test that API key is automatically generated"""
        self.assertIsNotNone(self.api_key.key)
        self.assertTrue(len(self.api_key.key) in [32, 64])

    def test_university_api_key_is_active(self):
        """Test the is_active field"""
        self.assertTrue(self.api_key.is_active)
        self.api_key.is_active = False
        self.api_key.save()
        self.assertFalse(self.api_key.is_active)