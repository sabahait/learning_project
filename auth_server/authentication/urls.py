# auth_server/authentication/urls.py
from django.urls import path
from .views import (
    RegisterAPIView, LoginAPIView, LogoutAPIView,
    VerifyTokenAPIView, RefreshTokenAPIView, UserProfileAPIView,
    CheckAuthAPIView, UpdateProfileAPIView, UpdatePasswordAPIView, UploadProfilePhotoAPIView
)

urlpatterns = [
    # API Endpoints
    path('register/', RegisterAPIView.as_view(), name='api_register'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('verify/', VerifyTokenAPIView.as_view(), name='api_verify'),
    path('refresh/', RefreshTokenAPIView.as_view(), name='api_refresh'),
    path('profile/', UserProfileAPIView.as_view(), name='api_profile'),
    path('check/', CheckAuthAPIView.as_view(), name='api_check_auth'),

    # VÉRIFIEZ QUE CES 3 LIGNES SONT BIEN PRÉSENTES :
    path('profile/update/', UpdateProfileAPIView.as_view(), name='api_profile_update'),
    path('profile/password/', UpdatePasswordAPIView.as_view(), name='api_profile_password'),
    path('profile/photo/', UploadProfilePhotoAPIView.as_view(), name='api_profile_photo'),
]