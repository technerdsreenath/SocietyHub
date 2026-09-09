from django import forms
from django.utils import timezone
from .models import Amenity, AmenityBooking
import datetime

class AmenityForm(forms.ModelForm):
    booking_fee = forms.DecimalField(
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )

    class Meta:
        model = Amenity
        fields = ['name', 'description', 'open_time', 'close_time', 'booking_fee']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
                'placeholder': 'e.g. Swimming Pool, Badminton Court, Community Hall',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
                'rows': 3,
                'placeholder': 'Description, capacity, guidelines, or rules for this amenity...',
                'required': True
            }),
            'open_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
                'required': True
            }),
            'close_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
                'required': True
            }),
        }

    def clean_booking_fee(self):
        fee = self.cleaned_data.get('booking_fee')
        if fee is None or fee == '':
            return 0.00
        return fee

    def clean(self):
        cleaned_data = super().clean()
        open_time = cleaned_data.get('open_time')
        close_time = cleaned_data.get('close_time')

        if open_time and close_time:
            if open_time >= close_time:
                raise forms.ValidationError("Closing time must be later than opening time.")
        return cleaned_data


class AmenityBookingForm(forms.ModelForm):
    class Meta:
        model = AmenityBooking
        fields = ['booking_date', 'start_time', 'end_time']
        widgets = {
            'booking_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
                'min': datetime.date.today().isoformat()
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary font-medium text-portal-text',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.amenity = kwargs.pop('amenity', None)
        self.current_booking_id = kwargs.pop('booking_id', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if booking_date and start_time and end_time:
            # Check if booking date is in the past
            if booking_date < datetime.date.today():
                raise forms.ValidationError("You cannot book an amenity for a past date.")

            # Check if start time is after or equal to end time
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")

            # If today, check if start time is in the past
            if booking_date == datetime.date.today():
                now_time = datetime.datetime.now().time()
                if start_time < now_time:
                    raise forms.ValidationError("You cannot book a slot in the past.")

            # Check operating hours of the amenity
            if self.amenity:
                if start_time < self.amenity.open_time or end_time > self.amenity.close_time:
                    raise forms.ValidationError(
                        f"Booking must be within the amenity's operating hours "
                        f"({self.amenity.open_time.strftime('%I:%M %p')} to {self.amenity.close_time.strftime('%I:%M %p')})."
                    )

                # Check for overlap with already confirmed bookings
                overlapping = AmenityBooking.objects.filter(
                    amenity=self.amenity,
                    booking_date=booking_date,
                    status='Confirmed',
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )
                
                if self.current_booking_id:
                    overlapping = overlapping.exclude(id=self.current_booking_id)

                if overlapping.exists():
                    raise forms.ValidationError(
                        "The requested time slot overlaps with an already confirmed booking for this amenity."
                    )

        return cleaned_data
