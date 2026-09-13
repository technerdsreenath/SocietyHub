import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import PushSubscription
from .push import send_push_notification

class PWAAandPushTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="pwa_user",
            password="password123",
            first_name="PWA",
            last_name="Tester"
        )

    def test_manifest_view(self):
        response = self.client.get('/manifest.json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/manifest+json', response['Content-Type'])
        
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['name'], 'SocietyHub - Smart Housing Society')
        self.assertEqual(data['display'], 'standalone')
        self.assertTrue(len(data['icons']) >= 2)

    def test_service_worker_view(self):
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/javascript', response['Content-Type'])
        self.assertEqual(response.headers.get('Service-Worker-Allowed'), '/')
        content = response.content.decode('utf-8')
        self.assertIn('societyhub-pwa-v1', content)
        self.assertIn("self.addEventListener('push'", content)

    def test_offline_view(self):
        response = self.client.get('/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You're Currently Offline", response.content)

    def test_vapid_public_key_api(self):
        response = self.client.get('/api/push/vapid-key/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('publicKey', data)
        self.assertTrue(len(data['publicKey']) > 20)

    def test_push_subscribe_and_unsubscribe_api(self):
        self.client.login(username="pwa_user", password="password123")

        payload = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-token-123",
            "keys": {
                "p256dh": "test_p256dh_key_sample_string",
                "auth": "test_auth_key_sample_string"
            }
        }

        # Subscribe
        response = self.client.post(
            '/api/push/subscribe/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        self.assertEqual(res_data['status'], 'success')

        # Verify DB
        sub = PushSubscription.objects.filter(user=self.user).first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.p256dh, "test_p256dh_key_sample_string")
        self.assertEqual(sub.auth, "test_auth_key_sample_string")

        # Unsubscribe
        unsub_payload = {"endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-token-123"}
        unsub_res = self.client.post(
            '/api/push/unsubscribe/',
            data=json.dumps(unsub_payload),
            content_type='application/json'
        )
        self.assertEqual(unsub_res.status_code, 200)
        self.assertFalse(PushSubscription.objects.filter(user=self.user).exists())

    @patch('pywebpush.webpush')
    def test_send_push_notification_dispatch(self, mock_webpush):
        # Create active subscription
        sub = PushSubscription.objects.create(
            user=self.user,
            endpoint="https://fcm.googleapis.com/fcm/send/fake-endpoint",
            p256dh="test_p256dh",
            auth="test_auth"
        )

        mock_webpush.return_value = None

        result = send_push_notification(
            user_or_users=self.user,
            title="Test Title",
            body="Test Body",
            url="/dashboard/"
        )

        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 0)
        self.assertTrue(mock_webpush.called)

    @patch('pywebpush.webpush')
    def test_push_test_api(self, mock_webpush):
        self.client.login(username="pwa_user", password="password123")
        PushSubscription.objects.create(
            user=self.user,
            endpoint="https://fcm.googleapis.com/fcm/send/fake-endpoint-2",
            p256dh="test_p256dh",
            auth="test_auth"
        )
        mock_webpush.return_value = None

        response = self.client.post('/api/push/test/')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        self.assertEqual(res_data['status'], 'success')


class RealTimeNotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="resident_user",
            password="password123",
            first_name="John",
            last_name="Resident"
        )
        self.client.login(username="resident_user", password="password123")

    def test_notification_creation_and_poll_api(self):
        from .models import Notification
        from .push import create_and_send_notification

        # Create two notifications for user
        res = create_and_send_notification(
            recipients=self.user,
            title="💳 Maintenance Bill Dispatched",
            message="Your maintenance bill for September 2026 is ₹2,500.",
            url="/billing/bill/101/",
            notification_type="bill"
        )
        self.assertEqual(res['in_app_created'], 1)

        # First poll with since_id=0
        poll_res = self.client.get('/api/notifications/poll/?since_id=0')
        self.assertEqual(poll_res.status_code, 200)
        data = json.loads(poll_res.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['unread_count'], 1)
        self.assertGreater(data['latest_id'], 0)

        # Subsequent poll with since_id=0 should return new item if since_id was previous id
        latest_id = data['latest_id']
        poll_res2 = self.client.get(f'/api/notifications/poll/?since_id={latest_id - 1}')
        data2 = json.loads(poll_res2.content)
        self.assertEqual(len(data2['new_notifications']), 1)
        self.assertEqual(data2['new_notifications'][0]['type'], 'bill')
        self.assertEqual(data2['new_notifications'][0]['url'], '/billing/bill/101/')

    def test_notifications_list_and_mark_read_apis(self):
        from .models import Notification

        n1 = Notification.objects.create(
            recipient=self.user,
            notification_type='notice',
            title="📢 Notice: Annual General Meeting",
            message="Meeting will be held this Sunday at 10 AM.",
            url="/notices/",
            is_read=False
        )
        n2 = Notification.objects.create(
            recipient=self.user,
            notification_type='report',
            title="📊 Audit Report: FY 2025-26",
            message="Official audit report uploaded.",
            url="/billing/audits/",
            is_read=False
        )

        # Fetch list
        list_res = self.client.get('/api/notifications/')
        self.assertEqual(list_res.status_code, 200)
        list_data = json.loads(list_res.content)
        self.assertEqual(list_data['unread_count'], 2)
        self.assertEqual(len(list_data['notifications']), 2)

        # Mark single as read
        mark_res = self.client.post(f'/api/notifications/{n1.id}/mark-read/')
        self.assertEqual(mark_res.status_code, 200)
        mark_data = json.loads(mark_res.content)
        self.assertEqual(mark_data['unread_count'], 1)

        n1.refresh_from_db()
        self.assertTrue(n1.is_read)

        # Mark all as read
        mark_all_res = self.client.post('/api/notifications/mark-all-read/')
        self.assertEqual(mark_all_res.status_code, 200)
        mark_all_data = json.loads(mark_all_res.content)
        self.assertEqual(mark_all_data['unread_count'], 0)

        n2.refresh_from_db()
        self.assertTrue(n2.is_read)
