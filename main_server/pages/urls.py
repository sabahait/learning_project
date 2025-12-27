# monprojet/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Importez TOUTES vos vues
from pages.views import (
    home, login_view, register_view, logout_view,
    auth_callback, test_auth,  # AJOUTEZ auth_callback et test_auth
    admin_courses, admin_users, admin_dashboard,
    dashboard,courses_available,profil,cours,historique
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('auth/login/', login_view, name='login'),
    path('auth/register/', register_view, name='register'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/callback/', auth_callback, name='auth_callback'),  # AJOUTEZ CETTE LIGNE
    path('test-auth/', test_auth, name='test_auth'),  # AJOUTEZ CETTE LIGNE
    
    # Pages principales
    path('', home, name='home'),
    
    # Dashboard et pages protégées
    path('administrateur/courses/', views.admin_courses, name='administrateur_courses'),
    path('administrateur/users/', views.admin_users, name='administrateur_users'),
    path('administrateur/dashboard/', views.admin_dashboard, name='administrateur_dashboard'),

# ============================================
# VUES UTILISATEUR
# ============================================

    path('dashboard/', views.dashboard, name='utilisateur_dashboard'),
    path('courses/', views.courses_available, name='courses_available'),
    path('profil/', views.profil, name='profil'),
    path('cours/', views.cours, name='cours'),
    path('historique/', views.historique, name='historique'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)