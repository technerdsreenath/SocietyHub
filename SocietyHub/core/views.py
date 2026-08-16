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
        # Add rich mock data for resident dashboard
        context.update({
            'bills': [
                {'id': 'B-102', 'type': 'Maintenance Fee', 'amount': '₹3,500', 'due_date': 'Aug 15, 2026', 'status': 'Unpaid', 'status_color': 'text-amber-600 bg-amber-50'},
                {'id': 'B-101', 'type': 'Clubhouse Booking Charge', 'amount': '₹1,500', 'due_date': 'Paid on Aug 01', 'status': 'Paid', 'status_color': 'text-green-600 bg-green-50'},
                {'id': 'B-099', 'type': 'Water & Utility surcharge', 'amount': '₹750', 'due_date': 'Paid on Jul 15', 'status': 'Paid', 'status_color': 'text-green-600 bg-green-50'},
            ],
            'notices': society_notices,  # <--- CHANGED: Replaced mock list with database queryset
            'bookings': [
                {'facility': 'Clubhouse Hall', 'date': 'Aug 15, 2026', 'time': '10:00 AM - 4:00 PM', 'status': 'Confirmed', 'status_class': 'text-green-600 border-green-200 bg-green-50'},
                {'facility': 'Tennis Court 2', 'date': 'Aug 08, 2026', 'time': '7:00 AM - 8:30 AM', 'status': 'Pending Approval', 'status_class': 'text-amber-600 border-amber-200 bg-amber-50'},
            ],
            'complaints': [
                {'title': 'Corridor Light Bulb Replacement', 'id': 'C-4890', 'date': 'Aug 06, 2026', 'status': 'Resolved', 'status_class': 'text-green-700 bg-green-50'},
                {'title': 'Elevator B Making Squeaking Sound', 'id': 'C-4895', 'date': 'Aug 07, 2026', 'status': 'In Progress', 'status_class': 'text-blue-700 bg-blue-50'},
            ]
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

        # If you have a Complaint model, replace this with: Complaint.objects.filter(society=profile.society, status!='Resolved').count()
        # For now, we set it to 0 or query your actual Complaint model if available:
        active_complaints_count = 0  # Change to your real query if you have a Complaint model

        context.update({
            'pending_count': pending_profiles.count(),
            'pending_approvals_count': pending_profiles.count(),
            'pending_profiles': pending_profiles,
            'approvals': pending_profiles,
            'active_complaints_count': active_complaints_count,
            'active_notices_count': society_notices.count(),
            'notices': society_notices[:2],  # Shows recent notices dynamically on the dashboard
        })
        return render(request, 'secretary/dashboard.html', context)
    
# Fetch real notices from the database for this society once
    society_notices = Notice.objects.filter(society=profile.society).order_by('-created_at')

    if role == 'chairperson':
        # Add mock data for chairperson dashboard
        context.update({
            'stats': {
                'total_residents': 148,
                'total_staff': 12,
                'maintenance_collection_rate': '92%',
                'monthly_revenue': '₹4,85,000',
                'monthly_expense': '₹3,20,000',
                'reserve_fund': '₹24,50,000'
            },
            'recent_transactions': [
                {'member': 'Aman Gupta', 'type': 'Maintenance Fee', 'amount': '₹3,500', 'date': 'Today, 2:30 PM', 'status': 'Success'},
                {'member': 'Meera Joshi', 'type': 'Clubhouse Booking', 'amount': '₹1,500', 'date': 'Yesterday, 11:15 AM', 'status': 'Success'},
                {'member': 'Rajesh Patil', 'type': 'Penalty (Late Payment)', 'amount': '₹500', 'date': 'Aug 05', 'status': 'Success'},
            ],
            'reports': [
                {'name': 'Q2 Financial Summary', 'type': 'PDF', 'size': '2.4 MB'},
                {'name': 'Biannual Audit Report 2026', 'type': 'PDF', 'size': '4.1 MB'},
                {'name': 'Security Audit & Visitor Trends', 'type': 'XLSX', 'size': '1.2 MB'}
            ],
            'notices': society_notices,
            'active_notices_count': society_notices.count(),
        })
        return render(request, 'chairperson/dashboard.html', context)

    elif role == 'security':
        # Add mock data for security dashboard
        context.update({
            'visitors': [
                {'name': 'Aditya Verma', 'contact': '+91 99988 87776', 'apartment': 'A-402', 'purpose': 'Delivery (Amazon)', 'entry_time': 'Today, 2:15 PM', 'status': 'Checked In', 'badge_color': 'bg-emerald-500'},
                {'name': 'Kabir Mehta', 'contact': '+91 98877 66554', 'apartment': 'C-101', 'purpose': 'Guest', 'entry_time': 'Today, 1:30 PM', 'status': 'Checked In', 'badge_color': 'bg-emerald-500'},
                {'name': 'Pooja Hegde', 'contact': '+91 97766 55443', 'apartment': 'B-304', 'purpose': 'Maintenance', 'entry_time': 'Today, 11:00 AM', 'status': 'Checked Out', 'badge_color': 'bg-gray-400'},
            ],
            'notices': society_notices,
            'active_notices_count': society_notices.count(),
        })
        return render(request, 'security/visitors.html', context)
    elif role == 'maintenance':
        # Add mock data for staff / maintenance dashboard
        context.update({
            'tasks': [
                {'id': 'T-1082', 'title': 'Inspect Elevator B squeaking noise', 'priority': 'High', 'location': 'Block B Lift Lobby', 'status': 'In Progress', 'status_color': 'text-blue-700 bg-blue-50'},
                {'id': 'T-1085', 'title': 'Fix water leakage in Block D ceiling', 'priority': 'High', 'location': 'Block D-501', 'status': 'Assigned', 'status_color': 'text-amber-700 bg-amber-50'},
                {'id': 'T-1079', 'title': 'Replace lobby bulb', 'priority': 'Low', 'location': 'Main Entrance Lobby', 'status': 'Completed', 'status_color': 'text-green-700 bg-green-50'},
            ]
        })
        return render(request, 'staff/tasks.html', context)

    else:
        if request.user.is_superuser:
            return redirect('admin:index')
        raise Http404("Invalid role configuration.")
