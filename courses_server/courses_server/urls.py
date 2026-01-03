# courses_server/urls.py - VERSION CORRIGÉE

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os  # Ajoutez cette importation

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('courses.urls')),
    path('', include('courses.urls')),  # Pour les autres URLs de l'app courses
]

# IMPORTANT: Cette ligne doit être au même niveau d'indentation que urlpatterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)