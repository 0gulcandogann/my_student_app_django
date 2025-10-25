from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def root_redirect(request):
    """Redirect root URL to login page if not authenticated, else to dashboard."""
    if request.session.get('user_id'):
        return redirect('dashboard')
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root'),  # Redirect root URL
    path('', include('student_management.urls')),  # Include student_management URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)