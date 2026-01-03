from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_info(request):
    return JsonResponse({
        'name': 'Auth Server API',
        'endpoints': {
            'login': 'POST /api/auth/login/',
            'register': 'POST /api/auth/register/',
            # ... autres endpoints
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('', api_info, name='api_home'),
]