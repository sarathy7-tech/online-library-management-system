from functools import wraps
from django.core.exceptions import PermissionDenied

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("You must be logged in.")
            
            user_role = request.user.role.role_name
            if user_role not in allowed_roles:
                raise PermissionDenied("You do not have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required('Admin')(view_func)


def librarian_required(view_func):
    return role_required('Admin', 'Librarian')(view_func)


def reader_required(view_func):
    return role_required('Reader')(view_func)