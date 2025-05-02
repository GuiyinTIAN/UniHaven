from django.test import TestCase

# Create your tests here.
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.timezone import now
from datetime import date
from accommodation.models import Accommodation, University, AccommodationRating, AccommodationUniversity,UniversityAPIKey, ReservationPeriod
import uuid


class AccommodationAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
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
            key="e6861bfe8eaa4994a8633222a136c78c",  
            is_active=True,
            last_used=now()
        )
        cls.cuhk_api_key = UniversityAPIKey.objects.create(
            university=cls.cuhk,
            key="586385e5a18c46e3a3a5c9162599320f",  
            is_active=True,
            last_used=now()
        )
        cls.hkust_api_key = UniversityAPIKey.objects.create(
            university=cls.hkust,
            key="96a847fd519845099624b757d22c7424", 
            is_active=True,
            last_used=now()
        )

        
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
        
        cls.accommodation_1.affiliated_universities.add(cls.hku, cls.hkust, cls.cuhk)
        cls.accommodation_2.affiliated_universities.add(cls.hku, cls.hkust)
        cls.accommodation_3.affiliated_universities.add(cls.cuhk)

    def test_home_page_json(self):
        """Test retrieving the home page returns the correct welcome message."""
        url = reverse('index')
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Welcome to UniHaven!")

    def test_accommodation_detail_api(self):
        """Test retrieving accommodation detail information via API."""
        
        url = f'/api/accommodation_detail/{self.accommodation_1.id}/'

        response = self.client.get(url, {"format":'json'})

       
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = {
            "id": self.accommodation_1.id,
            "title": self.accommodation_1.title,
            "description": self.accommodation_1.description,
            "type": self.accommodation_1.type,
            "beds": self.accommodation_1.beds,
            "bedrooms": self.accommodation_1.bedrooms,
            "price": f"{self.accommodation_1.price:.2f}",  
            "available_from": str(self.accommodation_1.available_from),
            "available_to": str(self.accommodation_1.available_to),
            "latitude": self.accommodation_1.latitude,  
            "longitude": self.accommodation_1.longitude,  
            "formatted_address": self.accommodation_1.formatted_address(), 
            "rating": self.accommodation_1.rating,  
            "reserved": self.accommodation_1.is_reserved(), 
            "region": self.accommodation_1.region,
            "university_codes": [ 
                self.hku.code,
                self.hkust.code,
                self.cuhk.code
            ],
            "reservation_periods": [  
            ],
            "available_periods": [
                {  
                "start_date" : "2025-05-01",
                "end_date" : "2025-10-01"
                }
            ]
        }
        self.assertEqual(response.json(), expected_data)
    def test_add_accommodation_1(self):
        """Test adding a new accommodation via API."""
        url = '/api/add-accommodation/?api_key=586385e5a18c46e3a3a5c9162599320f'

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

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_id = response.data['id']
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

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    

    
    

    def test_list_accommodation_with_filters(self):
        """Test listing accommodations with filter conditions."""
        url = '/api/list-accommodation/'
        params = {"type": "APARTMENT", "format": "json"}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["accommodations"]), 2)

    def test_list_accommodation_no_filters(self):
        """Test listing accommodations without filters returns all results."""
        url = '/api/list-accommodation/'
        params = {"format": "json"}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["accommodations"]), Accommodation.objects.count())

    def test_list_accommodation_user_id_filter(self):
        """Test listing accommodations filtered by user ID."""
        url = '/api/list-accommodation/'
        params = {"user_id": "HKUST_123", "format": "json"}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        accommodations = response.json()["accommodations"]
        for accommodation in accommodations:
            self.assertIn(accommodation["id"], [self.accommodation_1.id, self.accommodation_2.id])

    def test_list_accommodation_order_by_price(self):
        """Test listing accommodations sorted by ascending price."""
        url = '/api/list-accommodation/'
        params = {"order_by": "price_asc", "format": "json"}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        accommodations = response.json()["accommodations"]
        prices = [float(accommodation["price"]) for accommodation in accommodations]
        self.assertEqual(prices, sorted(prices))

    def test_list_accommodation_price_filter(self):
        """Test listing accommodations filtered by maximum price."""
        url = '/api/list-accommodation/'
        params = {"max_price": 5000, "format": "json"}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        accommodations = response.json()["accommodations"]
        prices = [float(accommodation["price"]) for accommodation in accommodations]
        self.assertEqual(len(prices), 2)

    def test_list_accommodation_date_filter(self):
        """Test listing accommodations filtered by available date range."""
        url = '/api/list-accommodation/'
        params = {
            "available_from": "2025-05-01", 
            "available_to": "2025-06-01", 
            "format": "json"}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        accommodations = response.json()["accommodations"]
        self.assertTrue(all(
            accommodation["available_from"] <= "2025-05-01" and accommodation["available_to"] >= "2025-06-01"
            for accommodation in accommodations
        ))

    def test_reserve_accommodation_success_post(self):
        """Test successfully reserving an accommodation via POST request."""
        url = reverse('reserve_accommodation')
        query_params = f"&User%20ID=CUHK_789&contact_number=123&end_date=2025-9-30&id={self.accommodation_1.id}&start_date=2025-8-02"
        full_url = f"{url}?{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.accommodation_1.refresh_from_db()
        self.assertFalse(self.accommodation_1.is_reserved())
        self.assertEqual(self.accommodation_1.reservation_periods.count(), 1)

        """Test reserving already reserved accommodation should fail."""
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reserve_accommodation_only_for_specified_university_post(self):
        """Test that reservation is allowed only for specified universities."""
        url = reverse('reserve_accommodation')
        query_params = f"&User%20ID=CUHK_789&contact_number=123&end_date=2025-9-30&id={self.accommodation_2.id}&start_date=2025-8-02"
        full_url = f"{url}?{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_reservation_success(self):
        """Test successfully canceling a reservation."""
        url = reverse('reserve_accommodation')
        query_params = f"&User%20ID=CUHK_789&contact_number=123&end_date=2025-9-30&id={self.accommodation_1.id}&start_date=2025-08-02"
        full_url = f"{url}?{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('cancel_reservation')
        query_params = f"&User%20ID=CUHK_789&id={self.accommodation_1.id}&reservation_id=1"
        full_url = f"{url}?{query_params}"
        response = self.client.put(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["success"])
        expected_message = 'Reservation for accommodation "Luxury Apartment" from 2025-08-02 to 2025-09-30 has been canceled.'
        self.assertEqual(response.json()["message"], expected_message)
        self.accommodation_1.refresh_from_db()
        self.assertFalse(self.accommodation_1.is_reserved())

    def test_cancel_reservation_wrong_user(self):
        """Test canceling reservation by a non-owner user should fail."""
        url = reverse('reserve_accommodation')
        query_params = f"&User%20ID=CUHK_789&contact_number=123&end_date=2025-9-30&id={self.accommodation_1.id}&start_date=2025-08-02"
        full_url = f"{url}?{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('cancel_reservation')
        query_params = f"&User%20ID=CUHK_890&id={self.accommodation_1.id}&reservation_id=1"
        full_url = f"{url}?{query_params}"
        response = self.client.put(full_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_reservation_not_found(self):
        """Test canceling a reservation for a non-existing accommodation."""
        url = reverse('cancel_reservation')
        query_params = f"&User%20ID=CUHK_890&id=99999&reservation_id=1"
        full_url = f"{url}?{query_params}"
        response = self.client.put(full_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "No Accommodation matches the given query.")

    def test_cancel_reservation_not_reserved(self):
        """Test canceling when there is no reservation should fail."""
        url = reverse('cancel_reservation')
        query_params = f"&User%20ID=CUHK_890&id={self.accommodation_1.id}&reservation_id=1"
        full_url = f"{url}?{query_params}"
        response = self.client.put(full_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {
            "success": False,
            "message": "Reservation not found."
        })

    def test_submit_rating_success(self):
        """Test submitting a rating successfully."""
        url = reverse('reserve_accommodation')
        query_params = f"&User%20ID=CUHK_789&contact_number=123&end_date=2025-9-30&id={self.accommodation_1.id}&start_date=2025-08-02"
        full_url = f"{url}?{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('rate_accommodation', args=[self.accommodation_1.id])
        query_params = "?rating=5&userid=CUHK_789"
        full_url = f"{url}{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.accommodation_1.refresh_from_db()
        self.assertEqual(self.accommodation_1.rating, 5.0)
        self.assertEqual(self.accommodation_1.rating_count, 1)
        self.assertEqual(self.accommodation_1.rating_sum, 5)

    
    def test_submit_invalid_rating_value(self):
        """Test submitting an invalid rating value (out of valid range)."""
        url = reverse('reserve_accommodation')  
        query_params = f"&User%20ID=CUHK_789&contact_number=123&end_date=2025-9-30&id={self.accommodation_1.id}&start_date=2025-08-02"  # 添加contact_number
        
        full_url = f"{url}?{query_params}"
        response = self.client.post(full_url) 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  
        query_params = "?rating=6&userid=CUHK_789"  
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_submit_rating_not_found(self):
        """Test submitting a rating for a non-existent accommodation."""
        url = reverse('rate_accommodation', args=[9999])  
        query_params = "?rating=5&userid=HKU_123"
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_submit_rating_already_rated(self):
        """Test submitting a rating for an accommodation that has already been rated by the user."""
        url = reverse('reserve_accommodation')  
        query_params = f"&User%20ID=CUHK_789&contact_number=123&end_date=2025-9-30&id={self.accommodation_1.id}&start_date=2025-08-02"  # 添加contact_number
        
        full_url = f"{url}?{query_params}"
        
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id]) 
        query_params = "?rating=5&userid=CUHK_789"
        full_url = f"{url}{query_params}"

        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  
        query_params = "?rating=5&userid=CUHK_789"
        full_url = f"{url}{query_params}"
        response = self.client.post(full_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_rating_not_reserved_by_user(self):
        """Test submitting a rating for an accommodation that has not been reserved by the user."""
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  
        query_params = "?rating=5&userid=CUHK_789"
        full_url = f"{url}{query_params}"
        response = self.client.post(full_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        expected_response = {
            "success": False,
            "message": "You can only rate accommodations you have reserved."
        }
        self.assertEqual(response.json(), expected_response)
    
    def test_submit_rating_missing_parameters(self):
        """Test submitting a rating with missing parameters."""
        url = reverse('rate_accommodation', args=[self.accommodation_1.id])  
        response = self.client.post(f"{url}?userid=HKU_123")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lookup_address_success(self):
        """Test successfully retrieving address information from the lookup API."""
        url = reverse('lookup_address')  
        query_params = "?address=princeton%20tower"
        full_url = f"{url}{query_params}"

        response = self.client.get(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data.get('EnglishAddress'))

        english_address = data['EnglishAddress']
        self.assertEqual(english_address['BuildingName'], "PRINCETON TOWER")
        self.assertEqual(english_address['StreetName'], "DES VOEUX ROAD WEST")
        self.assertEqual(english_address['BuildingNo'], "88")
        self.assertEqual(english_address['District'], "CENTRAL & WESTERN DISTRICT")
        self.assertEqual(english_address['Region'], "HK")

    def test_remove_university_association(self):
        """Test removing university association when multiple universities are linked."""
        api_key = self.hku_api_key.key
        url = f"/api/delete-accommodation/?api_key={api_key}&id={self.accommodation_1.id}"
        
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
       
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(
            response.json()["message"],
            f"Removed {self.hku.name}'s association with accommodation '{self.accommodation_1.title}'. The accommodation is still available to other universities."
        )
        self.assertFalse(self.accommodation_1.affiliated_universities.filter(id=self.hku.id).exists())
        
        self.assertTrue(self.accommodation_1.affiliated_universities.filter(id=self.hkust.id).exists())
        self.assertTrue(self.accommodation_1.affiliated_universities.filter(id=self.cuhk.id).exists())

    def test_delete_accommodation_when_all_associations_removed(self):
        """Test deleting the accommodation when the last university association is removed."""
        api_key = self.cuhk_api_key.key
        url = f"/api/delete-accommodation/?api_key={api_key}&id={self.accommodation_3.id}"
        
        response = self.client.delete(url, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(
            response.json()["message"],
            f"Accommodation '{self.accommodation_3.title}' has been completely deleted."
        )
        self.assertFalse(Accommodation.objects.filter(id=self.accommodation_3.id).exists())

    def test_accommodation_not_found(self):
        """Test deleting a non-existent accommodation should return an error."""
        api_key = "586385e5a18c46e3a3a5c9162599320f"
        url = f"/api/delete-accommodation/?api_key={api_key}&id=999"
        
        response = self.client.delete(url, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(response.json()["message"], "An unexpected error occurred: No Accommodation matches the given query.")
    
    def test_distance_calculation(self):
        """Test calculating the distance of accommodations from the campus."""
        url = '/api/list-accommodation/'
        params = {
            "price": 2000,
            "type": "APARTMENT", 
            "format": "json",
            "distance": "5",  
            "campus": "HKU_main", 
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        print(response_data)

        accommodations = response_data.get("accommodations", [])
        self.assertGreater(len(accommodations), 0, "No accommodations found in the response.")
    
        first_accommodation = accommodations[0]
        print("title:",first_accommodation["title"])
        self.assertIn("distance", first_accommodation, "Distance key is missing in the accommodation data.")
        self.assertAlmostEqual(
            first_accommodation["distance"], 
            0.21358179659004045
        )

    def test_update_accommodation_success(self):
        """Test successfully updating accommodation details."""
        updated_data = {
            "title": "Test_9",
            "description": "123",
            "type": "APARTMENT",
            "price": 9517,
            "beds": 1,
            "bedrooms": 2,
            "available_from": "2025-05-02",
            "available_to": "2025-05-02",
            "building_name": "top",
            "room_number": "string",
            "floor_number": "string",
            "flat_number": "string",
            "contact_name": "string",
            "contact_phone": "string",
            "contact_email": "user@example.com"
        }
        url = f"/api/update_accommodation/{self.accommodation_1.id}"
        response = self.client.put(
            f"{url}?api_key={self.hku_api_key.key}",
            data=updated_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["message"], "Accommodation updated successfully.")
            
        self.accommodation_1.refresh_from_db()

        self.assertEqual(self.accommodation_1.title, updated_data["title"])
        self.assertEqual(self.accommodation_1.description, updated_data["description"])
        self.assertEqual(self.accommodation_1.type, updated_data["type"])
        self.assertEqual(int(self.accommodation_1.price), updated_data["price"])  
        self.assertEqual(self.accommodation_1.beds, updated_data["beds"])
        self.assertEqual(self.accommodation_1.bedrooms, updated_data["bedrooms"])
        self.assertEqual(str(self.accommodation_1.available_from), updated_data["available_from"])
        self.assertEqual(str(self.accommodation_1.available_to), updated_data["available_to"])
        self.assertEqual(self.accommodation_1.building_name, updated_data["building_name"])
        self.assertEqual(self.accommodation_1.room_number, updated_data["room_number"])
        self.assertEqual(self.accommodation_1.floor_number, updated_data["floor_number"])
        self.assertEqual(self.accommodation_1.flat_number, updated_data["flat_number"])
        self.assertEqual(self.accommodation_1.contact_name, updated_data["contact_name"])
        self.assertEqual(self.accommodation_1.contact_phone, updated_data["contact_phone"])
        self.assertEqual(self.accommodation_1.contact_email, updated_data["contact_email"])
    
    def test_list_accommodation_with_reservation_period_filters(self):
        """Test listing accommodations filtered by reservation period."""
        reservation_1 = ReservationPeriod.objects.create(
        accommodation= self.accommodation_3,
        user_id="CUHK_12345",
        start_date="2025-05-03",
        end_date="2025-05-05"
    )
        self.accommodation_3.reservation_periods.set([reservation_1])
        url = f'/api/list-accommodation/?api_key={self.cuhk_api_key.key}'
        params = {
            "reservation_end" : "2025-05-05",
            "reservation_start" :"2025-05-03", 
            "format": "json"
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["accommodations"]), 1) 
  
    


def generate_unique_code(base="UNI"):
    return f"{base}_{uuid.uuid4().hex[:6]}"

class UniversityModelTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            code=generate_unique_code("HKU"),
            name="The University of Hong Kong",
            specialist_email="specialist@hku.hk"
        )

    def test_university_str(self):
        """Test string representation of University."""
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
            available_from=date(2025, 1, 1),
            available_to=date(2025, 12, 31),
            building_name="利都楼",
            latitude=22.3,
            longitude=114.2
        )

    def test_accommodation_basic_fields(self):
        """Test basic fields of Accommodation."""
        self.assertEqual(self.accommodation.title, "Real Apartment")
        self.assertEqual(self.accommodation.price, 1500.00)

    def test_formatted_address(self):
        """Test formatted_address returns correct formatted string."""
        expected_address = "利都楼"
        self.assertEqual(self.accommodation.formatted_address(), expected_address)

    def test_get_available_periods_without_available_dates(self):
        """Test get_available_periods returns empty list if no available_from and available_to."""
        acc = Accommodation.objects.create(
            title="No Date Apartment",
            description="No available date test",
            type="HOUSE",
            beds=1,
            bedrooms=1,
            price=999.99,
            latitude=22.3,
            longitude=114.2,
            room_number="TestRoom999",
            floor_number="TestFloor9",
            flat_number="TestFlatZ",
            geo_address="Test Geo Address 999",
            available_from=None,
            available_to=None
        )

        periods = acc.get_available_periods()
        self.assertEqual(periods, [])

    def test_is_available_without_reservation(self):
        """Test is_available returns True when there is no reservation."""
        start = date(2025, 3, 1)
        end = date(2025, 3, 10)
        self.assertTrue(self.accommodation.is_available(start, end))

    def test_is_available_with_reservation(self):
        """Test is_available returns False when there is a reservation conflict."""
        ReservationPeriod.objects.create(
            accommodation=self.accommodation,
            user_id="user123",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 8)
        )
        self.assertFalse(self.accommodation.is_available(date(2025, 3, 4), date(2025, 3, 6)))

    def test_get_available_periods(self):
        """Test get_available_periods returns correct available periods with reservations."""
        ReservationPeriod.objects.create(
            accommodation=self.accommodation,
            user_id="user123",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10)
        )
        periods = self.accommodation.get_available_periods()
        self.assertIn((date(2025, 1, 1), date(2025, 3, 4)), periods)
        self.assertIn((date(2025, 3, 11), date(2025, 12, 31)), periods)

    def test_is_reserved_true(self):
        """Test is_reserved returns True when fully booked."""
        ReservationPeriod.objects.create(
            accommodation=self.accommodation,
            user_id="user999",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        self.assertTrue(self.accommodation.is_reserved())


class ReservationPeriodModelTest(TestCase):
    def setUp(self):
        self.accommodation = Accommodation.objects.create(
            title="Booking Test Apartment",
            description="Booking logic test",
            type="APARTMENT",
            beds=1,
            bedrooms=1,
            price=900,
            available_from=date(2025, 1, 1),
            available_to=date(2025, 12, 31),
            latitude=22.3,
            longitude=114.2
        )

    def test_reservation_period_str(self):
        """Test string representation of ReservationPeriod."""
        reservation = ReservationPeriod.objects.create(
            accommodation=self.accommodation,
            user_id="user111",
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 10)
        )
        self.assertIn("Booking Test Apartment", str(reservation))
        self.assertIn("2025-04-01", str(reservation))


class AccommodationRatingModelTest(TestCase):
    def setUp(self):
        self.accommodation = Accommodation.objects.create(
            title="Rating Apartment",
            description="Rating logic test",
            type="HOUSE",
            beds=1,
            bedrooms=1,
            price=2000.00,
            latitude=22.3,
            longitude=114.2,
        )

    def test_accommodation_rating_str(self):
        """Test string representation of AccommodationRating."""
        rating = AccommodationRating.objects.create(
            accommodation=self.accommodation,
            user_identifier="rater1",
            rating=5
        )
        self.assertEqual(str(rating), "rater1 rated Rating Apartment (5)")

    def test_rating_value_range(self):
        """Test that rating value must be between 0 and 5."""
        invalid_rating = AccommodationRating(
            accommodation=self.accommodation,
            user_identifier="rater2",
            rating=6
        )
        with self.assertRaises(ValidationError):
            invalid_rating.full_clean()


class AccommodationUniversityModelTest(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            code=generate_unique_code("CUHK"),
            name="The Chinese University of Hong Kong",
            specialist_email="housing@cuhk.edu.hk"
        )
        self.accommodation = Accommodation.objects.create(
            title="University Hostel",
            description="University housing test",
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
        """Test string representation of AccommodationUniversity."""
        expected_str = f"{self.accommodation.title} - {self.university.code}"
        self.assertEqual(str(self.accommodation_university), expected_str)

    def test_unique_accommodation_university(self):
        """Test that duplicate accommodation-university associations are not allowed."""
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
            specialist_email="housing@ust.hk"
        )
        self.api_key = UniversityAPIKey.objects.create(
            university=self.university
        )

    def test_university_api_key_str(self):
        """Test string representation of UniversityAPIKey."""
        expected_str = f"{self.university.name} API Key"
        self.assertEqual(str(self.api_key), expected_str)

    def test_university_api_key_auto_generate(self):
        """Test that API key is auto-generated if not provided."""
        self.assertIsNotNone(self.api_key.key)
        self.assertTrue(len(self.api_key.key) in [32, 64])

    def test_university_api_key_is_active(self):
        """Test is_active field behavior."""
        self.assertTrue(self.api_key.is_active)
        self.api_key.is_active = False
        self.api_key.save()
        self.assertFalse(self.api_key.is_active)