from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Accommodation, University, AccommodationRating, AccommodationUniversity, UniversityAPIKey
import uuid

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