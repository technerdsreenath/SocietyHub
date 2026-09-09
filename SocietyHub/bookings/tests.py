import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from SocietyHub.users.models import Society, UserProfile
from SocietyHub.bookings.models import Amenity
from SocietyHub.bookings.forms import AmenityForm

class AmenityCreationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.society = Society.objects.create(
            name="Green Valley Heights",
            area="Kandivali",
            city="Mumbai",
            is_approved=True
        )

        # Secretary User
        self.secretary_user = User.objects.create_user(username="secretary_jane", password="password123")
        self.secretary_profile = UserProfile.objects.create(
            user=self.secretary_user,
            society=self.society,
            role="secretary",
            is_approved=True
        )

        # Resident User
        self.resident_user = User.objects.create_user(username="resident_bob", password="password123")
        self.resident_profile = UserProfile.objects.create(
            user=self.resident_user,
            society=self.society,
            role="resident",
            is_approved=True
        )

    def test_amenity_form_valid(self):
        form_data = {
            'name': 'Badminton Court',
            'description': 'Indoor wooden court with floodlights. Non-marking shoes required.',
            'open_time': '06:00',
            'close_time': '22:00',
            'booking_fee': '0.00'
        }
        form = AmenityForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_amenity_form_invalid_timings(self):
        # close_time earlier than open_time
        form_data = {
            'name': 'Badminton Court',
            'description': 'Indoor wooden court.',
            'open_time': '20:00',
            'close_time': '08:00',
            'booking_fee': '0.00'
        }
        form = AmenityForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Closing time must be later than opening time.", form.non_field_errors())

    def test_secretary_can_add_amenity(self):
        self.client.login(username="secretary_jane", password="password123")
        response = self.client.post('/bookings/add/', {
            'name': 'Swimming Pool',
            'description': 'Olympic-sized swimming pool with dedicated lifeguards.',
            'open_time': '06:00',
            'close_time': '21:00',
            'next': 'portal_dashboard'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        amenity = Amenity.objects.filter(society=self.society, name='Swimming Pool').first()
        self.assertIsNotNone(amenity)
        self.assertEqual(amenity.description, 'Olympic-sized swimming pool with dedicated lifeguards.')
        self.assertEqual(amenity.open_time, datetime.time(6, 0))
        self.assertEqual(amenity.close_time, datetime.time(21, 0))
        self.assertTrue(amenity.is_active)

    def test_resident_cannot_add_amenity(self):
        self.client.login(username="resident_bob", password="password123")
        response = self.client.post('/bookings/add/', {
            'name': 'Unauthorized Gym',
            'description': 'Residents should not be able to create amenities.',
            'open_time': '06:00',
            'close_time': '22:00',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Amenity.objects.filter(name='Unauthorized Gym').exists())
