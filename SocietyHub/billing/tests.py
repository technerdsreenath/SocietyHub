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

    def test_custom_heads_in_auto_dispatch(self):
        config = get_or_create_schedule_config(self.society)
        config.custom_heads = [
            {'name': 'Lift Maintenance AMC', 'type': 'fixed', 'amount': 750.0},
            {'name': 'Solar Maintenance Fund', 'type': 'per_sqft', 'amount': 0.40}
        ]
        config.save()

        # Delete any previous transactions for clean test
        PaymentTransaction.objects.filter(society=self.society).delete()

        res = execute_auto_dispatch_for_society(self.society, force=True)
        self.assertTrue(res['dispatched'])

        tx = PaymentTransaction.objects.filter(society=self.society, user=self.user).first()
        self.assertIsNotNone(tx)
        breakdown = tx.get_breakdown()
        
        # Verify custom heads appear in breakdown
        lift_item = next((item for item in breakdown if item['particular'] == 'LIFT MAINTENANCE AMC'), None)
        solar_item = next((item for item in breakdown if item['particular'] == 'SOLAR MAINTENANCE FUND'), None)

        self.assertIsNotNone(lift_item, "Lift Maintenance AMC should be in itemized particulars")
        self.assertEqual(lift_item['amount'], 750.0)

        self.assertIsNotNone(solar_item, "Solar Maintenance Fund should be in itemized particulars")
        # 1000 sqft * 0.40 = 400.00
        self.assertEqual(solar_item['amount'], 400.0)


from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from SocietyHub.billing.models import AuditReport

class AuditReportTests(TestCase):
    def setUp(self):
        # Society 1
        self.society1 = Society.objects.create(name="Greenwood CHS", city="Mumbai", is_approved=True)
        self.chair1_user = User.objects.create_user(username="chair1", password="password123")
        self.chair1_profile = UserProfile.objects.create(
            user=self.chair1_user, society=self.society1, role="chairperson", is_approved=True
        )
        self.resident1_user = User.objects.create_user(username="resident1", password="password123")
        self.resident1_profile = UserProfile.objects.create(
            user=self.resident1_user, society=self.society1, role="resident", is_approved=True, flat_name="101"
        )

        # Society 2
        self.society2 = Society.objects.create(name="Bluebell CHS", city="Pune", is_approved=True)
        self.resident2_user = User.objects.create_user(username="resident2", password="password123")
        self.resident2_profile = UserProfile.objects.create(
            user=self.resident2_user, society=self.society2, role="resident", is_approved=True, flat_name="202"
        )

        # Create dummy file
        self.dummy_file = SimpleUploadedFile("audit_2025.pdf", b"%PDF-1.4 dummy audit report content", content_type="application/pdf")
        self.report1 = AuditReport.objects.create(
            society=self.society1,
            title="Greenwood Audit FY 2025",
            financial_year="2024-2025",
            auditor_name="M/s ABC & Co.",
            audit_date=datetime.date(2025, 6, 30),
            file=self.dummy_file,
            file_size_display="28 KB",
            uploaded_by=self.chair1_user
        )

    def test_society1_member_can_view_reports(self):
        self.client.login(username="resident1", password="password123")
        resp = self.client.get(reverse('audit_reports_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Greenwood Audit FY 2025")
        self.assertContains(resp, "2024-2025")
        # Resident should not see delete button
        self.assertNotContains(resp, reverse('delete_audit_report', args=[self.report1.id]))

    def test_chairperson_sees_upload_and_delete_controls(self):
        self.client.login(username="chair1", password="password123")
        resp = self.client.get(reverse('audit_reports_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Upload Audit Report")
        self.assertContains(resp, reverse('delete_audit_report', args=[self.report1.id]))

    def test_society_isolation_in_listing(self):
        # Resident of society 2 should NOT see Society 1's report
        self.client.login(username="resident2", password="password123")
        resp = self.client.get(reverse('audit_reports_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Greenwood Audit FY 2025")

    def test_society_member_can_download_audit_report(self):
        self.client.login(username="resident1", password="password123")
        resp = self.client.get(reverse('download_audit_report', args=[self.report1.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        content = b''.join(resp.streaming_content)
        self.assertIn(b'%PDF-1.4 dummy audit report content', content)

    def test_cross_society_download_is_blocked(self):
        # Resident of society 2 attempting to download Society 1's report gets 404
        self.client.login(username="resident2", password="password123")
        resp = self.client.get(reverse('download_audit_report', args=[self.report1.id]))
        self.assertEqual(resp.status_code, 404)

    def test_chairperson_can_upload_report(self):
        self.client.login(username="chair1", password="password123")
        upload_file = SimpleUploadedFile("audit_2026.pdf", b"%PDF-1.4 audit 2026", content_type="application/pdf")
        resp = self.client.post(reverse('upload_audit_report'), {
            'title': 'Greenwood Audit FY 2026',
            'financial_year': '2025-2026',
            'auditor_name': 'CA Sharma',
            'file': upload_file
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(AuditReport.objects.filter(title='Greenwood Audit FY 2026', society=self.society1).exists())

    def test_resident_cannot_upload_report(self):
        self.client.login(username="resident1", password="password123")
        upload_file = SimpleUploadedFile("hacked.pdf", b"bad", content_type="application/pdf")
        resp = self.client.post(reverse('upload_audit_report'), {
            'title': 'Unauthorized Audit',
            'financial_year': '2025-2026',
            'file': upload_file
        }, follow=True)
        # Should be forbidden or rejected
        self.assertFalse(AuditReport.objects.filter(title='Unauthorized Audit').exists())

