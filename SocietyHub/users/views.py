import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import (
    SecretaryRegistrationForm,
    SocietyAndChairpersonForm,
    UserRegistrationForm,
    UserProfileEditForm,
)
from .models import Society, UserProfile
from django.db import transaction


logger = logging.getLogger(__name__)

def safe_send_mail(subject, message, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {e}")


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'

    def get_success_url(self):
        user = self.request.user
        
        # Route users based on their role or superuser status
        if user.is_superuser:
            return reverse_lazy('superadmin_approvals')
        
        # Since other roles use the same core portal_dashboard view, redirect there
        profile = getattr(user, 'profile', None)
        if profile:
            if profile.role in ['chairperson', 'secretary', 'resident', 'security', 'maintenance']:
                return reverse_lazy('portal_dashboard')
        
        return super().get_success_url()


@login_required
def superadmin_approvals_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied.")
    
    pending_buildings = Society.objects.filter(is_approved=False)
    pending_chairpersons = UserProfile.objects.filter(role='chairperson', is_approved=False).select_related('user', 'society')
    
    return render(request, 'superadmin/approvals.html', {
        'pending_buildings': pending_buildings,
        'pending_chairpersons': pending_chairpersons
    })

@login_required
def approve_building(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    building = get_object_or_404(Society, pk=pk)
    building.is_approved = True
    building.save()
    
    # Notify chairperson(s) of this society
    chairpersons = UserProfile.objects.filter(society=building, role='chairperson').select_related('user')
    recipients = [chair.user.email for chair in chairpersons if chair.user.email]
    if recipients:
        safe_send_mail(
            subject="Society Approved - SocietyHub",
            message=f"Congratulations! Your society '{building.name}' has been approved by the platform administrator.",
            recipient_list=recipients
        )
        
    return redirect('superadmin_approvals')

@login_required
def reject_building(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    building = get_object_or_404(Society, pk=pk)
    building.delete()
    return redirect('superadmin_approvals')

@login_required
def approve_chairperson(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    chairperson_profile = get_object_or_404(UserProfile, pk=pk, role='chairperson')
    chairperson_profile.is_approved = True
    chairperson_profile.save()
    
    # Notify chairperson
    email = chairperson_profile.user.email
    if email:
        safe_send_mail(
            subject="Account Approved - SocietyHub",
            message="Dear Chairperson, your account registration has been approved by the platform administrator. You can now log in and manage your society.",
            recipient_list=[email]
        )
        
    return redirect('superadmin_approvals')

@login_required
def reject_chairperson(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    chairperson_profile = get_object_or_404(UserProfile, pk=pk, role='chairperson')
    user = chairperson_profile.user
    user.delete()
    return redirect('superadmin_approvals')


@login_required
def chairperson_approvals_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'chairperson':
        return HttpResponseForbidden("Access denied.")
    
    pending_secretaries = UserProfile.objects.filter(
        role='secretary', 
        society=profile.society, 
        is_approved=False
    ).select_related('user')
    
    return render(request, 'chairperson/approvals.html', {
        'pending_secretaries': pending_secretaries
    })

@login_required
def approve_secretary(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'chairperson':
        return HttpResponseForbidden()
    
    secretary_profile = get_object_or_404(
        UserProfile, 
        pk=pk, 
        role='secretary', 
        society=profile.society
    )
    secretary_profile.is_approved = True
    secretary_profile.save()
    
    # Notify secretary
    email = secretary_profile.user.email
    if email:
        safe_send_mail(
            subject="Account Approved - SocietyHub",
            message="Dear Secretary, your registration has been approved by the Chairperson. You can now log in to the portal.",
            recipient_list=[email]
        )
        
    return redirect('chairperson_approvals')

@login_required
def reject_secretary(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'chairperson':
        return HttpResponseForbidden()
    
    secretary_profile = get_object_or_404(
        UserProfile, 
        pk=pk, 
        role='secretary', 
        society=profile.society
    )
    user = secretary_profile.user
    user.delete()
    return redirect('chairperson_approvals')


@login_required
def secretary_approvals_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden("Access denied.")
    
    pending_residents = UserProfile.objects.filter(
        role='resident', 
        society=profile.society, 
        is_approved=False
    ).select_related('user')
    
    return render(request, 'secretary/approvals.html', {
        'pending_residents': pending_residents
    })

@login_required
def approve_resident(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden()
    
    resident_profile = get_object_or_404(
        UserProfile, 
        pk=pk, 
        role='resident', 
        society=profile.society
    )
    resident_profile.is_approved = True
    resident_profile.save()
    
    # Notify resident
    email = resident_profile.user.email
    if email:
        safe_send_mail(
            subject="Account Approved - SocietyHub",
            message="Dear Resident, your registration request has been approved by the Secretary. Welcome to the portal!",
            recipient_list=[email]
        )
        
    return redirect('secretary_approvals')

@login_required
def reject_resident(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden()
    
    resident_profile = get_object_or_404(
        UserProfile, 
        pk=pk, 
        role='resident', 
        society=profile.society
    )
    user = resident_profile.user
    user.delete()
    return redirect('secretary_approvals')
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
            # 1. Save user securely with hashed password if not already handled in form.save()
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            user.set_password(password)  # Crucial for proper authentication!
            user.save()

            # 2. Match form's 'flat_name' field correctly
            UserProfile.objects.create(
                user=user,
                society=form.cleaned_data.get('society'),
                role=form.cleaned_data.get('role'),
                contact=form.cleaned_data.get('contact'),
                flat_name=form.cleaned_data.get('flat_name', ''),  # Fixed from apartment_name
                area_sqft=form.cleaned_data.get('area_sqft', None),
                is_approved=False
            )
            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})

from django.db import transaction

def register_society_view(request):
    if request.method == 'POST':
        form = SocietyAndChairpersonForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # 1. Create the Society (Pending Superadmin Approval)
                society = Society.objects.create(
                    name=form.cleaned_data['society_name'],
                    area=form.cleaned_data['area'],
                    total_wings=form.cleaned_data['total_wings'],
                    is_approved=False
                )
                
                # 2. Create the Chairperson User (Secures password hashing)
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                
                # 3. Create Chairperson Profile linked to the Society
                UserProfile.objects.create(  # Fixed from Profile to UserProfile
                    user=user,
                    role='chairperson',
                    society=society,
                    is_approved=False
                )
            return redirect('login')
    else:
        form = SocietyAndChairpersonForm()
    return render(request, 'auth/register_society.html', {'form': form})


def register_secretary_view(request):
    if request.method == 'POST':
        form = SecretaryRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                UserProfile.objects.create(  # Fixed from Profile to UserProfile
                    user=user,
                    role='secretary',
                    society=form.cleaned_data['society'],
                    wing=form.cleaned_data['wing'],
                    is_approved=False
                )
            return redirect('login')
    else:
        form = SecretaryRegistrationForm()
    return render(request, 'auth/register_secretary.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')
@login_required
def profile_edit_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            user = request.user
            full_name = form.cleaned_data.get('full_name')
            if full_name:
                names = full_name.split(' ', 1)
                user.first_name = names[0]
                user.last_name = names[1] if len(names) > 1 else ''
            user.email = form.cleaned_data.get('email')
            user.save()

            form.save()
            return redirect('portal_dashboard')
    else:
        form = UserProfileEditForm(instance=profile)

    return render(request, 'auth/edit_profile.html', {'form': form, 'profile': profile})
@staff_member_required
def admin_approvals_view(request):
    # Fetch all user profiles awaiting approval
    pending_profiles = UserProfile.objects.filter(is_approved=False).select_related('user')
    return render(request, 'users/admin_approvals.html', {'pending_profiles': pending_profiles})

@staff_member_required
def approve_user_view(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id)
    profile.is_approved = True
    profile.save()
    
    # Notify user
    email = profile.user.email
    if email:
        safe_send_mail(
            subject="Account Approved - SocietyHub",
            message=f"Dear User, your account as a {profile.get_role_display()} has been approved.",
            recipient_list=[email]
        )
        
    return redirect('admin_approvals')