from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Amenity, AmenityBooking
from .forms import AmenityBookingForm, AmenityForm
import datetime

@login_required(login_url='login')
def amenity_list_view(request):
    try:
        profile = request.user.profile
    except Exception:
        messages.error(request, "User profile not found. Please contact administrator.")
        return redirect('portal_dashboard')

    if not profile.is_approved:
        return redirect('portal_dashboard')

    society = profile.society
    
    # Automatically pre-populate default amenities if none exist in the database for this society.
    # Amenities in a cooperative society are complimentary community assets funded via maintenance.
    if society and not Amenity.objects.filter(society=society).exists():
        default_amenities = [
            {
                'name': 'Clubhouse',
                'description': 'Spacious clubhouse for community gatherings, small events, and indoor recreation.',
                'booking_fee': 0.00,
                'open_time': datetime.time(9, 0),
                'close_time': datetime.time(22, 0),
            },
            {
                'name': 'Swimming Pool',
                'description': 'Standard size swimming pool with a clean filtration system and changing rooms.',
                'booking_fee': 0.00,
                'open_time': datetime.time(6, 0),
                'close_time': datetime.time(21, 0),
            },
            {
                'name': 'Tennis Court',
                'description': 'Outdoor concrete tennis court with professional netting and floodlights.',
                'booking_fee': 0.00,
                'open_time': datetime.time(7, 0),
                'close_time': datetime.time(20, 0),
            },
            {
                'name': 'Gymnasium',
                'description': 'Fully equipped fitness center with treadmills, dumbbells, and cardio machines.',
                'booking_fee': 0.00,
                'open_time': datetime.time(6, 0),
                'close_time': datetime.time(22, 0),
            },
            {
                'name': 'Guest Room',
                'description': 'Furnished air-conditioned guest suites for hosting visitors overnight.',
                'booking_fee': 0.00,
                'open_time': datetime.time(8, 0),
                'close_time': datetime.time(22, 0),
            }
        ]
        for item in default_amenities:
            Amenity.objects.create(
                society=society,
                name=item['name'],
                description=item['description'],
                booking_fee=item['booking_fee'],
                open_time=item['open_time'],
                close_time=item['close_time'],
                is_active=True
            )

    # Ensure all amenities for this society have booking_fee set to 0.00 as amenities are complimentary
    if society:
        Amenity.objects.filter(society=society, booking_fee__gt=0).update(booking_fee=0.00)

    from django.db.models import Prefetch
    today = datetime.date.today()
    confirmed_bookings = AmenityBooking.objects.filter(
        booking_date__gte=today,
        status='Confirmed'
    ).order_by('booking_date', 'start_time')

    amenities = Amenity.objects.filter(society=society, is_active=True).prefetch_related(
        Prefetch('bookings', queryset=confirmed_bookings, to_attr='active_bookings')
    ).order_by('name')
    form = AmenityBookingForm()

    return render(request, 'bookings/amenity_list.html', {
        'amenities': amenities,
        'form': form,
        'profile': profile,
        'role': profile.role,
    })

@login_required(login_url='login')
def book_amenity_view(request, amenity_id):
    try:
        profile = request.user.profile
    except Exception:
        messages.error(request, "User profile not found.")
        return redirect('portal_dashboard')

    if not profile.is_approved:
        return redirect('portal_dashboard')

    amenity = get_object_or_404(Amenity, id=amenity_id, is_active=True, society=profile.society)
    
    if request.method == 'POST':
        form = AmenityBookingForm(request.POST, amenity=amenity)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.amenity = amenity
            booking.user = request.user
            booking.status = 'Confirmed'
            booking.save()
            messages.success(request, f"Successfully booked {amenity.name} on {booking.date_display}!")
            return redirect('my_bookings')
        else:
            # Send validation error messages back through Django Messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    
    return redirect('amenity_list')

@login_required(login_url='login')
def my_bookings_view(request):
    try:
        profile = request.user.profile
    except Exception:
        messages.error(request, "User profile not found.")
        return redirect('portal_dashboard')

    if not profile.is_approved:
        return redirect('portal_dashboard')

    now = datetime.datetime.now()
    today = datetime.date.today()
    current_time = now.time()

    all_bookings = AmenityBooking.objects.filter(user=request.user).order_by('-booking_date', '-start_time')

    upcoming_bookings = []
    past_bookings = []

    for booking in all_bookings:
        if booking.status == 'Cancelled':
            past_bookings.append(booking)
        else:
            is_upcoming = False
            if booking.booking_date > today:
                is_upcoming = True
            elif booking.booking_date == today:
                if booking.end_time >= current_time:
                    is_upcoming = True

            if is_upcoming:
                upcoming_bookings.append(booking)
            else:
                past_bookings.append(booking)

    return render(request, 'bookings/my_bookings.html', {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'profile': profile,
        'role': profile.role,
    })

@login_required(login_url='login')
def cancel_booking_view(request, booking_id):
    try:
        profile = request.user.profile
    except Exception:
        messages.error(request, "User profile not found.")
        return redirect('portal_dashboard')

    if not profile.is_approved:
        return redirect('portal_dashboard')

    # Allow cancellation if user is the booking owner OR a committee member in the same society
    if profile.role in ['chairperson', 'secretary']:
        booking = get_object_or_404(AmenityBooking, id=booking_id, amenity__society=profile.society)
    else:
        booking = get_object_or_404(AmenityBooking, id=booking_id, user=request.user)

    today = datetime.date.today()
    now_time = datetime.datetime.now().time()

    is_upcoming = False
    if booking.booking_date > today:
        is_upcoming = True
    elif booking.booking_date == today:
        if booking.start_time > now_time:
            is_upcoming = True

    if not is_upcoming:
        messages.error(request, "You cannot cancel a past or already started booking.")
    elif booking.status == 'Cancelled':
        messages.warning(request, "This booking is already cancelled.")
    else:
        booking.status = 'Cancelled'
        booking.save()
        messages.success(request, f"Booking for {booking.amenity.name} has been successfully cancelled.")

    # Redirect back based on query parameter
    next_url = request.GET.get('next', 'my_bookings')
    if next_url == 'society_bookings':
        return redirect('society_bookings')
    return redirect('my_bookings')


@login_required(login_url='login')
def society_bookings_view(request):
    try:
        profile = request.user.profile
    except Exception:
        messages.error(request, "User profile not found.")
        return redirect('portal_dashboard')

    if not profile.is_approved:
        return redirect('portal_dashboard')

    if profile.role not in ['chairperson', 'secretary']:
        messages.error(request, "Access denied. Only committee members can view all society bookings.")
        return redirect('portal_dashboard')

    society_bookings = AmenityBooking.objects.filter(
        amenity__society=profile.society
    ).select_related('amenity', 'user', 'user__profile').order_by('-booking_date', '-start_time')

    return render(request, 'bookings/society_bookings.html', {
        'bookings': society_bookings,
        'profile': profile,
        'role': profile.role,
    })


@login_required(login_url='login')
def edit_amenity_price_view(request, amenity_id):
    try:
        profile = request.user.profile
    except Exception:
        messages.error(request, "User profile not found.")
        return redirect('portal_dashboard')

    if not profile.is_approved:
        return redirect('portal_dashboard')

    if profile.role != 'chairperson':
        messages.error(request, "Access denied. Only the chairperson can modify amenity pricing.")
        return redirect('amenity_list')

    amenity = get_object_or_404(Amenity, id=amenity_id, society=profile.society)
    
    if request.method == 'POST':
        new_fee = request.POST.get('booking_fee')
        try:
            amenity.booking_fee = float(new_fee)
            amenity.save()
            messages.success(request, f"Successfully updated booking fee for {amenity.name} to ₹{amenity.booking_fee}!")
        except (ValueError, TypeError):
            messages.error(request, "Invalid booking fee value. Please enter a valid decimal number.")
            
    return redirect('amenity_list')


@login_required(login_url='login')
def add_amenity_view(request):
    try:
        profile = request.user.profile
    except Exception:
        messages.error(request, "User profile not found.")
        return redirect('portal_dashboard')

    if not profile.is_approved:
        return redirect('portal_dashboard')

    if profile.role not in ['secretary', 'chairperson']:
        messages.error(request, "Access denied. Only committee members can add amenities.")
        return redirect('portal_dashboard')

    society = profile.society
    if not society:
        messages.error(request, "You are not assigned to any society.")
        return redirect('portal_dashboard')

    next_url = request.POST.get('next') or request.GET.get('next') or 'portal_dashboard'

    if request.method == 'POST':
        form = AmenityForm(request.POST)
        if form.is_valid():
            amenity = form.save(commit=False)
            amenity.society = society
            amenity.is_active = True
            if amenity.booking_fee is None:
                amenity.booking_fee = 0.00
            amenity.save()
            messages.success(request, f"Amenity '{amenity.name}' has been successfully added to {society.name}!")
            if next_url == 'amenity_list':
                return redirect('amenity_list')
            return redirect('portal_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = "Form" if field == '__all__' else field.replace('_', ' ').capitalize()
                    messages.error(request, f"{field_name}: {error}")
            if next_url == 'amenity_list':
                return redirect('amenity_list')
            elif next_url == 'portal_dashboard':
                return redirect('portal_dashboard')
            return render(request, 'bookings/add_amenity.html', {
                'form': form,
                'profile': profile,
                'role': profile.role,
                'society': society,
                'next': next_url,
            })

    form = AmenityForm()
    return render(request, 'bookings/add_amenity.html', {
        'form': form,
        'profile': profile,
        'role': profile.role,
        'society': society,
        'next': next_url,
    })

