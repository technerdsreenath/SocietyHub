from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Society

class UserRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(max_length=50, label="Full Name")
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    # Society & Role Selection fields
    society = forms.ModelChoiceField(
        queryset=Society.objects.filter(is_approved=True), 
        label="Select Approved Society",
        empty_label="Choose your society..."
    )
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, label="Select Role")
    
    # Profile specific details
    contact = forms.CharField(max_length=15)
    apartment_name = forms.CharField(max_length=100, required=False, label="Apartment Name")
    area_sqft = forms.DecimalField(max_digits=8, decimal_places=2, required=False, label="Area (sqft)")

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        role = cleaned_data.get("role")
        
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
            
        # Enforce apartment and area requirements specifically for residents
        if role == 'resident':
            if not cleaned_data.get("apartment_name"):
                self.add_error('apartment_name', "Apartment name is required for residents.")
            if not cleaned_data.get("area_sqft"):
                self.add_error('area_sqft', "Area in sqft is required for maintenance calculations.")
                
        return cleaned_data