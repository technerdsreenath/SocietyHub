from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegistrationForm
from .models import UserProfile
from django.contrib.admin.views.decorators import staff_member_required



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('portal_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            UserProfile.objects.create(
                user=user,
                society=form.cleaned_data.get('society'),
                role=form.cleaned_data.get('role'),
                contact=form.cleaned_data.get('contact'),
                apartment_name=form.cleaned_data.get('apartment_name', ''),
                area_sqft=form.cleaned_data.get('area_sqft', None),
                is_society_approved=False
            )
            return redirect('login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'auth/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@staff_member_required
def admin_approvals_view(request):
    # Fetch all user profiles awaiting approval
    pending_profiles = UserProfile.objects.filter(is_society_approved=False).select_related('user')
    return render(request, 'users/admin_approvals.html', {'pending_profiles': pending_profiles})

@staff_member_required
def approve_user_view(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)
    profile.is_society_approved = True
    profile.save()
    return redirect('admin_approvals')