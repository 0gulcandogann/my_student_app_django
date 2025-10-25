from django.shortcuts import redirect
from django.contrib import messages
from .models import User
import uuid

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to access this page')
            return redirect('login')

        try:
            user_id = uuid.UUID(user_id)
            user = User.objects.get(id=user_id)
        except (ValueError, User.DoesNotExist):
            messages.error(request, 'Invalid session. Please log in again.')
            request.session.flush()
            return redirect('login')
        except Exception:
            messages.error(request, 'An unexpected error occurred. Please try again later.')
            return redirect('login')

        if not user.is_admin:
            messages.error(request, 'You do not have permission to access this page')
            return redirect('unauthorized')

        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapper