from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Allow superusers / platform admins full access
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            user_role = getattr(request.user.profile, 'role', None)
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
                
            raise PermissionDenied("You do not have permission to view this page.")
        return _wrapped_view
    return decorator