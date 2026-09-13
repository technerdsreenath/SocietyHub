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
from django.contrib import messages

from .forms import (
    SecretaryRegistrationForm,
    SocietyAndChairpersonForm,
    UserRegistrationForm,
    UserProfileEditForm,
)
from .models import Society, UserProfile, Notice
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
        'profile': profile,
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
def portal_dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return redirect('login')
    
    context = {'profile': profile}
    
    if profile.role == 'secretary':
        pending_profiles = UserProfile.objects.filter(
            role__in=['resident', 'security', 'maintenance'], 
            society=profile.society, 
            is_approved=False
        ).select_related('user')
        
        # --- ADD THESE PRINT STATEMENTS ---
        print("--- DEBUG DASHBOARD ---")
        print("Secretary:", request.user.username)
        print("Society:", profile.society)
        print("Pending Count Found:", pending_profiles.count())
        for p in pending_profiles:
            print(" - Pending User:", p.user.username, "| Society:", p.society, "| Approved:", p.is_approved)
        print("-----------------------")
        
        from SocietyHub.complaints.models import Complaint
        active_complaints_count = Complaint.objects.filter(society=profile.society).exclude(status='Closed').count()
        
        from SocietyHub.users.models import Notice
        society_notices = Notice.objects.filter(society=profile.society).order_by('-created_at')

        from SocietyHub.bookings.models import Amenity
        from SocietyHub.bookings.forms import AmenityForm
        amenities = Amenity.objects.filter(society=profile.society, is_active=True).order_by('name')
        amenity_form = AmenityForm()

        context.update({
            'pending_profiles': pending_profiles,
            'pending_count': pending_profiles.count(),
            'pending_approvals_count': pending_profiles.count(),
            'approvals': pending_profiles,
            'active_complaints_count': active_complaints_count,
            'active_notices_count': society_notices.count(),
            'notices': society_notices[:2],
            'amenities': amenities,
            'amenity_form': amenity_form,
        })
        
    return render(request, 'secretary/dashboard.html', context)

def validate_notice_datetime(notice_date_str, notice_time_str):
    import datetime
    from django.utils import timezone
    
    parsed_date = None
    parsed_time = None
    
    if notice_date_str:
        try:
            parsed_date = datetime.datetime.strptime(notice_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    if notice_time_str:
        try:
            parsed_time = datetime.datetime.strptime(notice_time_str, '%H:%M').time()
        except ValueError:
            try:
                parsed_time = datetime.datetime.strptime(notice_time_str, '%H:%M:%S').time()
            except ValueError:
                pass
                
    if parsed_time and not parsed_date:
        return False, "Please select a date if you are setting a time."
                
    if parsed_date:
        local_now = timezone.localtime(timezone.now())
        current_date = local_now.date()
        current_time = local_now.time()
        
        if parsed_date < current_date:
            return False, "You cannot select a past date."
        elif parsed_date == current_date and parsed_time:
            if parsed_time.replace(second=0, microsecond=0) < current_time.replace(second=0, microsecond=0):
                return False, "You cannot select a past time for today."
                
    return True, None

@login_required
def secretary_notices_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        status = request.POST.get('status', 'Published')
        notice_date = request.POST.get('notice_date') or None
        notice_time = request.POST.get('notice_time') or None
        
        if title and content:
            is_valid, error_msg = validate_notice_datetime(notice_date, notice_time)
            if not is_valid:
                messages.error(request, error_msg)
            else:
                notice = Notice.objects.create(
                    society=profile.society,
                    title=title,
                    content=content,
                    status=status,
                    notice_date=notice_date,
                    notice_time=notice_time
                )
                if status == 'Published':
                    try:
                        from SocietyHub.core.push import notify_society_notice
                        notify_society_notice(notice)
                    except Exception:
                        pass
                messages.success(request, "Notice published successfully!")
            return redirect('secretary_notices')

    notices = Notice.objects.filter(society=profile.society).order_by('-created_at')
    
    context = {
        'profile': profile,
        'notices': notices,
    }
    return render(request, 'secretary/notices.html', context)

@login_required
def notices_list_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return HttpResponseForbidden("Access denied.")
    
    notices = Notice.objects.filter(society=profile.society).order_by('-created_at')
    
    context = {
        'profile': profile,
        'notices': notices,
    }
    return render(request, 'notices/notices_list.html', context)

@login_required
def edit_notice_view(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden("Access denied.")
    
    notice = get_object_or_404(Notice, pk=pk, society=profile.society)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        status = request.POST.get('status', 'Published')
        notice_date = request.POST.get('notice_date') or None
        notice_time = request.POST.get('notice_time') or None
        
        if title and content:
            is_valid, error_msg = validate_notice_datetime(notice_date, notice_time)
            if not is_valid:
                messages.error(request, error_msg)
            else:
                notice.title = title
                notice.content = content
                notice.status = status
                notice.notice_date = notice_date
                notice.notice_time = notice_time
                notice.save()
                messages.success(request, "Notice updated successfully!")
            
    return redirect('secretary_notices')

@login_required
def chairperson_dashboard(request):
    try:
        profile = request.user.profile
        society = profile.society
        # Fetch notices for this specific society
        notices = Notice.objects.filter(society=society).order_by('-created_at')
    except (UserProfile.DoesNotExist, AttributeError):
        notices = []
        profile = None

    context = {
        'profile': profile,
        'notices': notices,
    }
    return render(request, 'chairperson_dashboard.html', context)

@login_required
def secretary_approvals_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden()
    
    pending_profiles = UserProfile.objects.filter(
        role__in=['resident', 'security', 'maintenance'],
        society=profile.society, 
        is_approved=False
    ).select_related('user')
    
    context = {
        'profile': profile,  # <-- Added this so 'profile' exists in context
        'pending_profiles': pending_profiles
    }
    return render(request, 'secretary/approvals.html', context)

@login_required
def approve_resident(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden()
    
    # CHANGE: Allow resident, security, and maintenance roles
    resident_profile = get_object_or_404(
        UserProfile, 
        pk=pk, 
        role__in=['resident', 'security', 'maintenance'], 
        society=profile.society
    )
    resident_profile.is_approved = True
    resident_profile.save()
    
    # Notify user
    email = resident_profile.user.email
    if email:
        safe_send_mail(
            subject="Account Approved - SocietyHub",
            message=f"Dear {resident_profile.get_role_display()}, your registration request has been approved by the Secretary. Welcome to the portal!",
            recipient_list=[email]
        )
        
    return redirect('secretary_approvals')

@login_required
def reject_resident(request, pk):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'secretary':
        return HttpResponseForbidden()
    
    # CHANGE: Allow resident, security, and maintenance roles
    resident_profile = get_object_or_404(
        UserProfile, 
        pk=pk, 
        role__in=['resident', 'security', 'maintenance'], 
        society=profile.society
    )
    user = resident_profile.user
    user.delete()
    return redirect('secretary_approvals')


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # 1. Save user securely with hashed password
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
                flat_name=form.cleaned_data.get('flat_name', ''),  
                area_sqft=form.cleaned_data.get('area_sqft', None),
                wing=form.cleaned_data.get('wing'),
                flat_number=form.cleaned_data.get('flat_number'),
                is_approved=False
            )
            return redirect('login')
    else:
        form = UserRegistrationForm()

    # Fetch societies so your template's {% for s in societies %} loop works
    societies = Society.objects.all()

    return render(request, 'auth/register.html', {
        'form': form,
        'societies': societies
    })

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
                    city=form.cleaned_data['city'],
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

@login_required
def directory_view(request):
    try:
        profile = request.user.profile
    except Exception:
        return HttpResponseForbidden("You do not have an active profile.")

    if not profile.is_approved:
        return render(request, 'auth/pending_approval.html', {'profile': profile})

    # Fetch all approved profiles in the same society
    members = UserProfile.objects.filter(
        society=profile.society,
        is_approved=True
    ).select_related('user')

    # Sorting hierarchy:
    # 1. Chairperson
    # 2. Secretary (wing-wise)
    # 3. Resident (wing-wise)
    # 4. Maintenance Staff
    # 5. Security Guard
    role_order = {
        'chairperson': 1,
        'secretary': 2,
        'resident': 3,
        'maintenance': 4,
        'security': 5,
    }

    sorted_members = sorted(
        members,
        key=lambda m: (
            role_order.get(m.role, 99),
            (m.wing or '').lower(),
            (m.flat_number or '').lower(),
            (m.user.get_full_name() or m.user.username).lower()
        )
    )

    context = {
        'profile': profile,
        'members': sorted_members,
        'role': profile.role,
    }
    return render(request, 'resident/directory.html', context)

@login_required
def change_resident_type(request, pk):
    try:
        profile = request.user.profile
    except Exception:
        return HttpResponseForbidden()

    if profile.role != 'secretary':
        return HttpResponseForbidden("Only secretaries are authorized to perform this action.")

    resident_profile = get_object_or_404(UserProfile, pk=pk, role='resident', society=profile.society)
    
    if request.method == 'POST':
        new_type = request.POST.get('resident_type')
        if new_type in ['owner', 'tenant']:
            resident_profile.resident_type = new_type
            resident_profile.save()
            messages.success(request, f"Successfully changed {resident_profile.user.get_full_name() or resident_profile.user.username} to {new_type.capitalize()}.")
        else:
            messages.error(request, "Invalid resident type selected.")

    return redirect('directory')