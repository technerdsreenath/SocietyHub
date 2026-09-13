import json
import logging
from django.conf import settings
from django.contrib.auth.models import User
from .models import PushSubscription, Notification

try:
    import pywebpush
except ImportError:
    pywebpush = None

logger = logging.getLogger(__name__)

def get_vapid_claims():
    return {
        "sub": getattr(settings, 'VAPID_CLAIM_EMAIL', 'mailto:sreenathnair4112@gmail.com')
    }

def send_push_notification(user_or_users, title, body, url='/dashboard/', tag=None, data=None):
    """
    Sends Web Push Notification to all active PushSubscriptions of given user(s).
    Automatically purges expired (HTTP 404 / 410 Gone) subscriptions.
    
    Returns:
        dict: {'sent': int, 'failed': int, 'cleaned': int}
    """
    if not pywebpush:
        logger.warning("[Push] pywebpush library is not installed. Skipping web push.")
        return {'sent': 0, 'failed': 0, 'cleaned': 0}

    vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
    if not vapid_private_key:
        logger.warning("[Push] Cannot send notification: VAPID_PRIVATE_KEY not configured in settings.")
        return {'sent': 0, 'failed': 0, 'cleaned': 0}

    vapid_claims = get_vapid_claims()

    # Normalize users query
    if isinstance(user_or_users, User):
        subscriptions = PushSubscription.objects.filter(user=user_or_users, is_active=True)
    elif hasattr(user_or_users, '__iter__'):
        subscriptions = PushSubscription.objects.filter(user__in=user_or_users, is_active=True)
    else:
        subscriptions = PushSubscription.objects.filter(is_active=True)

    if not subscriptions.exists():
        return {'sent': 0, 'failed': 0, 'cleaned': 0}

    payload = {
        "title": title,
        "body": body,
        "url": url,
        "icon": "/static/images/pwa-icon-192.png",
        "badge": "/static/images/badge-72.png",
        "tag": tag or "societyhub-alert",
    }
    if data and isinstance(data, dict):
        payload.update(data)

    payload_json = json.dumps(payload)

    sent = 0
    failed = 0
    cleaned = 0

    for sub in subscriptions:
        try:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth
                }
            }
            pywebpush.webpush(
                subscription_info=subscription_info,
                data=payload_json,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            sent += 1
        except pywebpush.WebPushException as ex:
            failed += 1
            status_code = getattr(ex.response, 'status_code', None) if getattr(ex, 'response', None) else None
            # HTTP 404 Not Found or 410 Gone indicates expired or revoked subscription
            if status_code in [404, 410]:
                sub.delete()
                cleaned += 1
                logger.info(f"[Push] Removed expired subscription {sub.id} (HTTP {status_code})")
            else:
                logger.warning(f"[Push] Failed to send push to subscription {sub.id}: {ex}")
        except Exception as e:
            failed += 1
            logger.error(f"[Push] Unexpected error sending push: {e}")

    return {'sent': sent, 'failed': failed, 'cleaned': cleaned}


def create_and_send_notification(recipients, title, message, url='/dashboard/', notification_type='general', society=None, tag=None):
    """
    Unified notification dispatch engine:
    1. Creates persistent In-App Notification records for all target recipients.
    2. Sends browser Web Push Notifications to all active subscribers among recipients.
    """
    # Normalize recipients into a list
    if isinstance(recipients, User):
        user_list = [recipients]
    elif hasattr(recipients, '__iter__'):
        user_list = list(recipients)
    else:
        user_list = []

    if not user_list:
        return {'in_app_created': 0, 'push_sent': 0}

    # 1. Store persistent In-App Notifications
    records = [
        Notification(
            recipient=u,
            society=society,
            notification_type=notification_type,
            title=title,
            message=message,
            url=url,
        )
        for u in user_list
    ]
    created = Notification.objects.bulk_create(records)

    # 2. Trigger Web Push Notifications (if subscribed)
    push_res = send_push_notification(
        user_or_users=user_list,
        title=title,
        body=message,
        url=url,
        tag=tag or f"{notification_type}-alert"
    )

    return {
        'in_app_created': len(created),
        'push': push_res
    }


# Society Workflow Helper Triggers
def notify_society_notice(notice):
    """
    Sends in-app and push notification to all approved residents and committee members in the society.
    """
    target_users = User.objects.filter(
        profile__society=notice.society,
        profile__is_approved=True
    ).distinct()

    title = f"📢 Notice: {notice.title}"
    body = f"{notice.content[:110]}..." if len(notice.content) > 110 else notice.content
    url = "/notices/"
    return create_and_send_notification(
        recipients=target_users,
        title=title,
        message=body,
        url=url,
        notification_type='notice',
        society=notice.society,
        tag=f"notice-{notice.id}"
    )


def notify_maintenance_bill(payment_transaction):
    """
    Sends in-app and push notification to flat owner when an itemized maintenance bill is generated/dispatched.
    """
    title = f"💳 Maintenance Bill Dispatched"
    body = f"Bill #{payment_transaction.bill_number or payment_transaction.id} for {payment_transaction.billing_period} totaling ₹{payment_transaction.amount:,.2f} is generated."
    url = f"/billing/bill/{payment_transaction.id}/"
    return create_and_send_notification(
        recipients=payment_transaction.user,
        title=title,
        message=body,
        url=url,
        notification_type='bill',
        society=payment_transaction.society,
        tag=f"bill-{payment_transaction.id}"
    )


def notify_audit_report(report):
    """
    Sends in-app and push notification to all society members when an official audit/financial report is published.
    """
    target_users = User.objects.filter(
        profile__society=report.society,
        profile__is_approved=True
    ).distinct()

    title = f"📊 Audit Report: {report.title}"
    fy_info = f" for {report.financial_year}" if report.financial_year else ""
    body = f"Official statutory audit report{fy_info} is now published and available to download."
    url = "/billing/audits/"
    return create_and_send_notification(
        recipients=target_users,
        title=title,
        message=body,
        url=url,
        notification_type='report',
        society=report.society,
        tag=f"report-{report.id}"
    )


def notify_complaint_update(complaint):
    """
    Sends in-app and push notification to resident when complaint status changes.
    """
    if complaint.resident and complaint.resident.user:
        title = f"🛠️ Complaint Update - #{complaint.id}"
        body = f"Your complaint '{complaint.title[:30]}' status changed to {complaint.get_status_display()}."
        url = "/complaints/"
        return create_and_send_notification(
            recipients=complaint.resident.user,
            title=title,
            message=body,
            url=url,
            notification_type='complaint',
            society=complaint.society,
            tag=f"complaint-{complaint.id}"
        )
    return None
