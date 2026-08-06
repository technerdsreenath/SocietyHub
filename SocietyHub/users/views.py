from django.shortcuts import render, redirect
from SocietyHub.users.forms import UserRegistrationForm
from SocietyHub.users.models import UserProfile

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            UserProfile.objects.create(
                user=user,
                society=form.cleaned_data['society'],
                role=form.cleaned_data['role'],
                contact=form.cleaned_data['contact'],
                apartment_name=form.cleaned_data.get('apartment_name', ''),
                area_sqft=form.cleaned_data.get('area_sqft', None),
                is_society_approved=False  # Requires Chairperson/Secretary approval
            )
            return redirect('login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'users/register.html', {'form': form})