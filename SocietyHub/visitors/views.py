from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from .models import Visitor

@login_required
def check_in_visitor(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'security':
        return HttpResponseForbidden("Access denied.")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        apartment = request.POST.get('apartment')
        purpose = request.POST.get('purpose')
        
        if name and contact and apartment and purpose:
            Visitor.objects.create(
                society=profile.society,
                name=name,
                contact=contact,
                apartment=apartment,
                purpose=purpose,
                status='Checked In'
            )
    return redirect('portal_dashboard')

@login_required
def check_out_visitor(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'security':
        return HttpResponseForbidden("Access denied.")
    
    visitor = get_object_or_404(Visitor, pk=pk, society=profile.society)
    visitor.status = 'Checked Out'
    visitor.exit_time = timezone.now()
    visitor.save()
    
    return redirect('portal_dashboard')

@login_required
def visitor_log_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'security':
        return HttpResponseForbidden("Access denied.")
    
    # Filter selection
    filter_type = request.GET.get('filter', 'all')
    
    # Base query for the guard's society
    queryset = Visitor.objects.filter(society=profile.society).order_by('-entry_time')
    
    now = timezone.now()
    
    if filter_type == 'today':
        today = timezone.localdate()
        queryset = queryset.filter(entry_time__date=today)
    elif filter_type == '7_days':
        seven_days_ago = now - timedelta(days=7)
        queryset = queryset.filter(entry_time__gte=seven_days_ago)
    elif filter_type == '30_days':
        thirty_days_ago = now - timedelta(days=30)
        queryset = queryset.filter(entry_time__gte=thirty_days_ago)
        
    context = {
        'profile': profile,
        'visitors': queryset,
        'current_filter': filter_type,
    }
    return render(request, 'security/visitor_log.html', context)
