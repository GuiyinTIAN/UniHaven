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
            # reserved=False,
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
            # reserved=False,
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
            available_from="2025-04-26",
            available_to="2025-05-08",
            # reserved=False,
            building_name="kennedy Town",
            room_number="C3003",
            flat_number="C",
            floor_number="30",
            latitude=22.28367,
            longitude=114.12809,
            # reservation_periods =[
            # {
            # "id": 10,
            # "start_date": "2025-04-28",
            # "end_date": "2025-05-01",
            # "user_id": "HKUST_123"
            # }
            # ],
            # available_periods =[
            # {
            # "start_date": "2025-04-26",
            # "end_date": "2025-04-27"
            # },
            # {
            # "start_date": "2025-05-02",
            # "end_date": "2025-05-08"
            # }
            # ]
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
            "id": self.accommodation_1.id,
            "title": self.accommodation_1.title,
            "description": self.accommodation_1.description,
            "type": self.accommodation_1.type,
            "beds": self.accommodation_1.beds,
            "bedrooms": self.accommodation_1.bedrooms,
            "price": f"{self.accommodation_1.price:.2f}",  # 确保价格格式为字符串，带两位小数
            "available_from": str(self.accommodation_1.available_from),
            "available_to": str(self.accommodation_1.available_to),
            "latitude": self.accommodation_1.latitude,  # 假设存在 latitude 字段
            "longitude": self.accommodation_1.longitude,  # 假设存在 longitude 字段
            "formatted_address": self.accommodation_1.formatted_address(),  # 假设有 formatted_address 方法
            "rating": self.accommodation_1.rating,  # 假设存在 rating 字段
            "reserved": self.accommodation_1.is_reserved(),  # 假设存在 reserved 字段
            "region": self.accommodation_1.region,
            "university_codes": [  # 修改为仅包含大学代码
                self.hku.code,
                self.hkust.code,
                self.cuhk.code
            ],
            "reservation_periods": [  # 假设存在 reservation_periods 字段
            ],
            "available_periods": [
                {  # 假设存在 available_periods 字段
                "start_date" : "2025-05-01",
                "end_date" : "2025-10-01"
                }
            ]
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
            "building_name": "PRINCETON TOWER",
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
        self.assertEqual(accommodation.building_name, data['building_name'])
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