import datetime
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from SocietyHub.users.models import Society, UserProfile
from SocietyHub.bookings.models import Amenity
from SocietyHub.billing.models import MaintenanceScheduleConfig, PaymentTransaction
from SocietyHub.billing.utils import get_or_create_schedule_config, execute_auto_dispatch_for_society

class AutoDispatchAndAmenityTests(TestCase):
    def setUp(self):
        self.society = Society.objects.create(
            name="Test Palms CHS",
            area="Bandra",
            city="Mumbai",
            is_approved=True
        )
        self.user = User.objects.create_user(username="testresident", password="password123")
        self.profile = UserProfile.objects.create(
            user=self.user,
            society=self.society,
            role="resident",
            is_approved=True,
            flat_name="Flat 101",
            wing="A",
            flat_number="101",
            area_sqft=Decimal("1000.00")
        )

    def test_amenity_free_rate(self):
        amenity = Amenity.objects.create(
            society=self.society,
            name="Clubhouse",
            description="Free clubhouse",
            booking_fee=Decimal("0.00"),
            open_time=datetime.time(9, 0),
            close_time=datetime.time(22, 0)
        )
        self.assertEqual(amenity.booking_fee, Decimal("0.00"))

    def test_schedule_config_creation(self):
        config = get_or_create_schedule_config(self.society)
        self.assertIsNotNone(config)
        self.assertTrue(config.is_auto_dispatch_active)
        self.assertEqual(config.dispatch_day, 1)
        next_d = config.get_next_dispatch_date()
        self.assertIsInstance(next_d, datetime.date)

    def test_auto_dispatch_execution(self):
        # Force dispatch for current cycle
        res = execute_auto_dispatch_for_society(self.society, force=True)
        self.assertTrue(res['dispatched'])
        self.assertEqual(res['created_count'], 1)
        self.assertGreater(res['total_amount'], Decimal('0'))

        # Verify PaymentTransaction created
        tx = PaymentTransaction.objects.filter(society=self.society, user=self.user).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.payment_type, 'maintenance')
        self.assertEqual(tx.status, 'pending')
        self.assertTrue('Auto Dispatched' in tx.remarks)
