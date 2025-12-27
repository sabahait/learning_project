from django.urls import path
from .views import (
    RegisterAPIView, LoginAPIView, LogoutAPIView,
    VerifyTokenAPIView, RefreshTokenAPIView, UserProfileAPIView,
    CheckAuthAPIView
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api_register'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('verify/', VerifyTokenAPIView.as_view(), name='api_verify'),
    path('refresh/', RefreshTokenAPIView.as_view(), name='api_refresh'),
    path('profile/', UserProfileAPIView.as_view(), name='api_profile'),
    path('check/', CheckAuthAPIView.as_view(), name='api_check_auth'),
]