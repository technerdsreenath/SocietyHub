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
        
        # Add empty data lists for resident dashboard (no backend models for bills/bookings yet)
        context.update({
            'bills': [],
            'notices': society_notices,
            'bookings': [],
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
        # Fetch real dynamic stats for chairperson dashboard
        total_residents = UserProfile.objects.filter(society=profile.society, role='resident', is_approved=True).count()
        total_staff = UserProfile.objects.filter(society=profile.society, role__in=['security', 'maintenance'], is_approved=True).count()
        context.update({
            'stats': {
                'total_residents': total_residents,
                'total_staff': total_staff,
                'maintenance_collection_rate': '0%',
                'monthly_revenue': '₹0',
                'monthly_expense': '₹0',
                'reserve_fund': '₹0'
            },
            'recent_transactions': [],
            'reports': [],
            'notices': society_notices,
            'active_notices_count': society_notices.count(),
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
        assigned_tasks = Complaint.objects.filter(assigned_to=request.user, society=profile.society).exclude(status='Closed').order_by('-created_at')
        
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
            })
            
        context.update({
            'tasks': mapped_tasks
        })
        return render(request, 'staff/tasks.html', context)

    else:
        if request.user.is_superuser:
            return redirect('admin:index')
        raise Http404("Invalid role configuration.")
