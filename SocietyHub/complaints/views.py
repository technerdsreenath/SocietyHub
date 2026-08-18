from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Complaint

@login_required
def complaints_list_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return HttpResponseForbidden("Access denied.")
    
    role = profile.role
    society = profile.society
    
    # 1. Filed by current user (for Resident, Chairperson, Secretary)
    my_complaints = Complaint.objects.filter(created_by=request.user, society=society).order_by('-created_at')
    
    # 2. All complaints in the society (for Secretary, Maintenance, Security)
    all_complaints = []
    my_tasks = []
    
    if role in ['secretary', 'maintenance', 'security', 'chairperson']:
        all_complaints = Complaint.objects.filter(society=society).order_by('-created_at')
        
    if role in ['maintenance', 'security']:
        # Complaints assigned to the current staff/security user
        my_tasks = Complaint.objects.filter(assigned_to=request.user, society=society).order_by('-created_at')
        
    context = {
        'profile': profile,
        'my_complaints': my_complaints,
        'all_complaints': all_complaints,
        'my_tasks': my_tasks,
        'role': role,
    }
    return render(request, 'complaints/complaints_list.html', context)

@login_required
def create_complaint_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role not in ['resident', 'chairperson', 'secretary']:
        return HttpResponseForbidden("Access denied.")
        
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        
        if title and description and category:
            Complaint.objects.create(
                society=profile.society,
                created_by=request.user,
                title=title,
                description=description,
                category=category,
                status='Pending'
            )
            messages.success(request, "Complaint registered successfully!")
            return redirect('complaints_list')
            
    return redirect('complaints_list')

@login_required
def accept_complaint_view(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role not in ['maintenance', 'security']:
        return HttpResponseForbidden("Access denied.")
        
    complaint = get_object_or_404(Complaint, pk=pk, society=profile.society)
    if complaint.status == 'Pending':
        complaint.status = 'In Progress'
        complaint.assigned_to = request.user
        complaint.save()
        messages.success(request, f"You have accepted the complaint: {complaint.title}")
    return redirect('complaints_list')

@login_required
def complete_complaint_view(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role not in ['maintenance', 'security']:
        return HttpResponseForbidden("Access denied.")
        
    complaint = get_object_or_404(Complaint, pk=pk, society=profile.society, assigned_to=request.user)
    if complaint.status == 'In Progress':
        complaint.status = 'Completed'
        complaint.save()
        messages.success(request, f"Complaint marked as completed/done: {complaint.title}")
    return redirect('complaints_list')

@login_required
def close_complaint_view(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role not in ['maintenance', 'security']:
        return HttpResponseForbidden("Access denied.")
        
    complaint = get_object_or_404(Complaint, pk=pk, society=profile.society, assigned_to=request.user)
    if complaint.status in ['In Progress', 'Completed']:
        complaint.status = 'Closed'
        complaint.save()
        messages.success(request, f"Complaint marked as closed: {complaint.title}")
    return redirect('complaints_list')

@login_required
def approve_complaint_resolution(request, pk, feedback):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role not in ['resident', 'chairperson', 'secretary']:
        return HttpResponseForbidden("Access denied.")
    
    complaint = get_object_or_404(Complaint, pk=pk, society=profile.society, created_by=request.user)
    if complaint.status == 'Closed':
        if feedback == 'yes':
            complaint.status = 'Approved'
            complaint.save()
            messages.success(request, f"Thank you for confirming! Complaint '{complaint.title}' has been marked as approved.")
        elif feedback == 'no':
            complaint.status = 'Pending'  # Reopen it back to Pending
            complaint.assigned_to = None  # Remove assignment
            complaint.save()
            messages.warning(request, f"Complaint '{complaint.title}' has been reopened and returned to the active queue.")
            
    return redirect('complaints_list')
