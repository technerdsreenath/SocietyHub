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

        # Fetch all amenity bookings for the secretary's society
        from SocietyHub.bookings.models import AmenityBooking
        society_bookings = AmenityBooking.objects.filter(
            amenity__society=profile.society
        ).select_related('amenity', 'user', 'user__profile').order_by('-booking_date', '-start_time')

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
            'reports': [],
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
