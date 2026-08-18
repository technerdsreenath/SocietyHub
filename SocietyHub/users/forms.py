from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Society
from django.contrib.auth import get_user_model

User = get_user_model()

class SecretaryRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150,required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chairperson Username'}))
    email = forms.EmailField(required=True,widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Chairperson Email'}))
    password = forms.CharField(
    required=True, 
    widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
)
    society = forms.ModelChoiceField(queryset=Society.objects.filter(is_approved=True), widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select Approved Society'}))
    wing = forms.CharField(max_length=50,required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wing (e.g., Wing A)'}))

class SocietyAndChairpersonForm(forms.Form):
    # Society Details
    society_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Society Name'}))
    area = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Area / Location'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    total_wings = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Wings'}))
    
    # Chairperson Account Details
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chairperson Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Chairperson Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserProfileEditForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150, 
        required=False, 
        label="Full Name", 
        widget=forms.TextInput(attrs={'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary'})
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary'})
    )
    society_name = forms.CharField(
        required=False, 
        disabled=True, 
        label="Assigned Society", 
        widget=forms.TextInput(attrs={'class': 'w-full bg-gray-100 border border-portal-border rounded-xl px-3.5 py-2.5 text-xs text-gray-500 cursor-not-allowed'})
    )

    class Meta:
        model = UserProfile
        fields = ['wing', 'flat_number', 'flat_name', 'contact', 'area_sqft']
        widgets = {
            'wing': forms.TextInput(attrs={'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary'}),
            'flat_number': forms.TextInput(attrs={'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary'}),
            'flat_name': forms.TextInput(attrs={'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary'}),
            'contact': forms.TextInput(attrs={'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary'}),
            'area_sqft': forms.NumberInput(attrs={'class': 'w-full bg-[#F8F9FA] border border-portal-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:ring-2 focus:ring-portal-primary'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['full_name'].initial = self.instance.user.get_full_name()
            self.fields['email'].initial = self.instance.user.email
        if self.instance and self.instance.society:
            self.fields['society_name'].initial = self.instance.society.name

        # Lock core property/flat details for residents so they cannot change them
        if self.instance and self.instance.role == 'resident':
            self.fields['wing'].disabled = True
            self.fields['flat_number'].disabled = True
            self.fields['flat_name'].disabled = True
            self.fields['area_sqft'].disabled = True

        # Lock wing for secretaries as well
        if self.instance and self.instance.role == 'secretary':
            self.fields['wing'].disabled = True

        # Automatically add disabled styling classes if a field is disabled
        for field_name, field in self.fields.items():
            if field.disabled:
                field.widget.attrs.update({
                    'class': 'w-full bg-gray-100 border border-portal-border rounded-xl px-3.5 py-2.5 text-xs text-gray-500 cursor-not-allowed',
                    'tabindex': '-1'
                })
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
    role = forms.ChoiceField(
        choices=[(val, label) for val, label in UserProfile.ROLE_CHOICES if val != 'chairperson'],
        label="Select Role"
    )
    
    # Profile specific details
    wing = forms.CharField(max_length=50, required=False, label="Wing (e.g., Wing A)")
    flat_number = forms.CharField(max_length=20, required=False, label="Flat Number")
    contact = forms.CharField(max_length=15)
    
    flat_name = forms.CharField(max_length=100, required=False, label="Flat name")
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
    
            if not cleaned_data.get("area_sqft"):
                self.add_error('area_sqft', "Area in sqft is required for maintenance calculations.")
                
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name')
        if full_name:
            names = full_name.split(' ', 1)
            user.first_name = names[0]
            if len(names) > 1:
                user.last_name = names[1]
        user.set_password(self.cleaned_data.get('password'))
        if commit:
            user.save()
        return user