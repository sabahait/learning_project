# auth_server/urls.py - VERSION COMPLÈTE

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from authentication.views import LoginView, RegisterView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Page d'accueil de l'auth_server
    path('', RedirectView.as_view(url='/login/', permanent=False), name='auth_home'),
    
    # Pages HTML pour l'authentification
    path('login/', LoginView.as_view(), name='login_html'),
    path('register/', RegisterView.as_view(), name='register_html'),
    path('logout/', LogoutView.as_view(), name='logout_html'),
    
    # API REST (préfixe api/)
    path('api/auth/', include('authentication.urls')),
]