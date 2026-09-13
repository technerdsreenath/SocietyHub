from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from SocietyHub.users.models import UserProfile,Notice

@login_required(login_url='login')
def portal_dashboard(request):
    try:
        profile = request.user.profile
    except Exception:
        if request.user.is_superuser:
            return redirect('admin:index')
        return render(request, 'auth/pending_approval.html', {
            'error': 'You do not have an active profile. Please contact the administrator.'
        })

    # If the user's profile is not approved yet
    if not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    role = profile.role
    context = {'profile': profile}

    # Fetch real notices from the database for this society once
    society_notices = Notice.objects.filter(society=profile.society).order_by('-created_at')

    if role == 'resident':
        # Fetch real complaints from the database for this resident
        from SocietyHub.complaints.models import Complaint
        user_complaints = Complaint.objects.filter(created_by=request.user, society=profile.society).order_by('-created_at')[:5]
        
        # Fetch real bookings from the database for this resident
        from SocietyHub.bookings.models import AmenityBooking
        user_bookings = AmenityBooking.objects.filter(user=request.user).order_by('-booking_date', '-start_time')[:5]
        
        # Fetch real payment transactions for this resident
        from SocietyHub.billing.models import PaymentTransaction
        user_payments = PaymentTransaction.objects.filter(user=request.user, society=profile.society).order_by('-created_at')[:5]
        
        context.update({
            'bills': user_payments,
            'notices': society_notices,
            'bookings': user_bookings,
            'complaints': user_complaints
        })
        return render(request, 'resident/dashboard.html', context)

    elif role == 'secretary':
        # Fetch real pending approvals for this society from the database
        pending_profiles = UserProfile.objects.filter(
            role__in=['resident', 'security', 'maintenance'], 
            society=profile.society, 
            is_approved=False
        ).select_related('user')

        # Fetch real notices from the database for this society
        society_notices = Notice.objects.filter(society=profile.society).order_by('-created_at')

        # Fetch actual open/active complaints count
        from SocietyHub.complaints.models import Complaint
        active_complaints_count = Complaint.objects.filter(society=profile.society).exclude(status='Closed').count()

        # Fetch all amenity bookings and amenities for the secretary's society
        from SocietyHub.bookings.models import Amenity, AmenityBooking
        from SocietyHub.bookings.forms import AmenityForm
        society_bookings = AmenityBooking.objects.filter(
            amenity__society=profile.society
        ).select_related('amenity', 'user', 'user__profile').order_by('-booking_date', '-start_time')
        amenities = Amenity.objects.filter(society=profile.society, is_active=True).order_by('name')
        amenity_form = AmenityForm()

        # Fetch billing metrics for society
        from SocietyHub.billing.models import PaymentTransaction
        society_txns = PaymentTransaction.objects.filter(society=profile.society)
        total_collected = sum(t.amount for t in society_txns.filter(status='success'))
        pending_bills_count = society_txns.filter(status='pending').count()

        context.update({
            'pending_count': pending_profiles.count(),
            'pending_approvals_count': pending_profiles.count(),
            'pending_profiles': pending_profiles,
            'approvals': pending_profiles,
            'active_complaints_count': active_complaints_count,
            'active_notices_count': society_notices.count(),
            'notices': society_notices[:2],  # Shows recent notices dynamically on the dashboard
            'bookings': society_bookings,
            'amenities': amenities,
            'amenity_form': amenity_form,
            'total_collected': total_collected,
            'pending_bills_count': pending_bills_count,
        })
        return render(request, 'secretary/dashboard.html', context)
    
    # Fetch real notices from the database for this society once
    society_notices = Notice.objects.filter(society=profile.society).order_by('-created_at')

    if role == 'chairperson':
        # Fetch real dynamic stats for chairperson dashboard
        total_residents = UserProfile.objects.filter(society=profile.society, role='resident', is_approved=True).count()
        total_staff = UserProfile.objects.filter(society=profile.society, role__in=['security', 'maintenance'], is_approved=True).count()
        pending_secretaries = UserProfile.objects.filter(
            role='secretary',
            society=profile.society,
            is_approved=False
        ).select_related('user')
        # Fetch all amenity bookings for the chairperson's society
        from SocietyHub.bookings.models import AmenityBooking
        society_bookings = AmenityBooking.objects.filter(
            amenity__society=profile.society
        ).select_related('amenity', 'user', 'user__profile').order_by('-booking_date', '-start_time')

        # Real billing metrics for chairperson
        from SocietyHub.billing.models import PaymentTransaction
        chair_txns = PaymentTransaction.objects.filter(society=profile.society)
        chair_total_collected = sum(t.amount for t in chair_txns.filter(status='success'))
        total_bills_count = chair_txns.count()
        success_count = chair_txns.filter(status='success').count()
        collection_rate = f"{(success_count / total_bills_count * 100):.0f}%" if total_bills_count > 0 else "0%"

        recent_transactions = chair_txns.select_related('user', 'user__profile').order_by('-created_at')[:8]

        # Fetch real audit reports for chairperson's society
        from SocietyHub.billing.models import AuditReport
        from SocietyHub.billing.forms import AuditReportUploadForm
        society_audit_reports = AuditReport.objects.filter(society=profile.society).order_by('-audit_date', '-created_at')

        context.update({
            'stats': {
                'total_residents': total_residents,
                'total_staff': total_staff,
                'maintenance_collection_rate': collection_rate,
                'monthly_revenue': f"₹{chair_total_collected:,.2f}",
                'monthly_expense': '₹0',
                'reserve_fund': f"₹{chair_total_collected:,.2f}"
            },
            'recent_transactions': recent_transactions,
            'reports': society_audit_reports,
            'audit_upload_form': AuditReportUploadForm(),
            'notices': society_notices,
            'active_notices_count': society_notices.count(),
            'pending_secretaries': pending_secretaries,
            'bookings': society_bookings,
        })
        return render(request, 'chairperson/dashboard.html', context)

    elif role == 'security':
        # Fetch actual visitors from the database for the guard's society
        from SocietyHub.visitors.models import Visitor
        visitors = Visitor.objects.filter(society=profile.society).order_by('-entry_time')
        
        context.update({
            'visitors': visitors,
            'notices': society_notices,
            'active_notices_count': society_notices.count(),
        })
        return render(request, 'security/visitors.html', context)
    elif role == 'maintenance':
        # Fetch assigned complaints and map them to tasks for staff dashboard
        from SocietyHub.complaints.models import Complaint
        assigned_tasks = Complaint.objects.filter(assigned_to=request.user, society=profile.society).exclude(status__in=['Closed', 'Approved']).order_by('-created_at')
        
        mapped_tasks = []
        for comp in assigned_tasks:
            status_color = 'text-blue-700 bg-blue-50'
            if comp.status == 'Completed':
                status_color = 'text-green-700 bg-green-50'
                
            mapped_tasks.append({
                'title': comp.title,
                'id': f"C-{comp.id:04d}",
                'comp_id': comp.id,
                'priority': comp.category,
                'location': f"{comp.created_by.profile.wing or ''} - {comp.created_by.profile.flat_number or ''}",
                'status': comp.status,
                'status_color': status_color,
                'rejection_reason': comp.rejection_reason,
            })
            
        context.update({
            'tasks': mapped_tasks
        })
        return render(request, 'staff/tasks.html', context)

    else:
        if request.user.is_superuser:
            return redirect('admin:index')
        raise Http404("Invalid role configuration.")


# ---------------------------------------------------------
# PWA & Web Push Notification Views & APIs
# ---------------------------------------------------------
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from .models import PushSubscription
from .push import send_push_notification

def manifest_view(request):
    """
    Serves PWA manifest.json with official MIME type.
    """
    return render(request, 'manifest.json', content_type='application/manifest+json')


def service_worker_view(request):
    """
    Serves sw.js directly at /sw.js with root Service-Worker-Allowed header.
    """
    response = render(request, 'sw.js', content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def offline_view(request):
    """
    Renders offline fallback template when network is unreachable.
    """
    return render(request, 'offline.html')


@require_GET
def get_vapid_public_key_api(request):
    """
    Returns the public VAPID key for client-side subscription.
    """
    public_key = getattr(settings, 'VAPID_PUBLIC_KEY', '')
    return JsonResponse({'publicKey': public_key})


@login_required(login_url='login')
@require_POST
def push_subscribe_api(request):
    """
    Registers or updates the user's browser PushSubscription credentials.
    """
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            return JsonResponse({'status': 'error', 'message': 'Invalid subscription payload.'}, status=400)

        user_agent = request.META.get('HTTP_USER_AGENT', '')[:250]

        sub, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user,
                'p256dh': p256dh,
                'auth': auth,
                'user_agent': user_agent,
                'is_active': True,
            }
        )

        return JsonResponse({
            'status': 'success',
            'created': created,
            'message': 'Push subscription registered successfully.'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_POST
def push_unsubscribe_api(request):
    """
    Removes push subscription for the requesting user/endpoint.
    """
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        if endpoint:
            PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return JsonResponse({'status': 'success', 'message': 'Unsubscribed successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_POST
def push_test_api(request):
    """
    Sends an instant test push notification to the logged-in user.
    """
    user_name = request.user.first_name or request.user.username
    res = send_push_notification(
        user_or_users=request.user,
        title="🔔 SocietyHub Push Alert",
        body=f"Hello {user_name}! Push notifications and PWA offline sync are active on your device.",
        url="/dashboard/",
        tag="test-alert"
    )
    if res['sent'] > 0:
        return JsonResponse({'status': 'success', 'message': f"Test notification dispatched successfully! ({res['sent']} device/browser reached)"})
    else:
        return JsonResponse({
            'status': 'warning', 
            'message': "No active push subscription found for your browser. Click 'Enable Push Notifications' first."
        })


# ---------------------------------------------------------
# Real-Time In-App Notification APIs
# ---------------------------------------------------------
from .models import Notification

def serialize_notification(n):
    return {
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'url': n.url,
        'is_read': n.is_read,
        'time_ago': n.time_ago_display(),
        'created_at': n.created_at.isoformat(),
    }


@login_required(login_url='login')
@require_GET
def notifications_poll_api(request):
    """
    Real-time polling endpoint.
    Returns notifications newer than ?since_id=X and the current unread count.
    """
    try:
        since_id = int(request.GET.get('since_id', 0))
    except (ValueError, TypeError):
        since_id = 0

    qs = Notification.objects.filter(recipient=request.user)
    unread_count = qs.filter(is_read=False).count()
    latest_obj = qs.order_by('-id').first()
    latest_id = latest_obj.id if latest_obj else 0

    new_items = []
    if since_id > 0:
        new_qs = qs.filter(id__gt=since_id).order_by('id')
        new_items = [serialize_notification(n) for n in new_qs]

    return JsonResponse({
        'status': 'success',
        'unread_count': unread_count,
        'latest_id': latest_id,
        'new_notifications': new_items
    })


@login_required(login_url='login')
@require_GET
def notifications_list_api(request):
    """
    Returns list of recent notifications for the notification tray / modal.
    """
    qs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:25]
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({
        'status': 'success',
        'unread_count': unread_count,
        'notifications': [serialize_notification(n) for n in qs]
    })


@login_required(login_url='login')
@require_POST
def notification_mark_read_api(request, pk):
    """
    Marks an individual notification as read.
    """
    Notification.objects.filter(recipient=request.user, pk=pk).update(is_read=True)
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'status': 'success', 'unread_count': unread_count})


@login_required(login_url='login')
@require_POST
def notifications_mark_all_read_api(request):
    """
    Marks all unread notifications for the user as read.
    """
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success', 'unread_count': 0})

