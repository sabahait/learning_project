# payment_server/urls.py - AJOUTEZ la route pour la page d'accueil
from django.contrib import admin
from django.urls import path, include
from payments.views import payment_home, process_payment, verify_course_access, get_user_payment_history, get_saved_payment_methods

urlpatterns = [
    # Page d'accueil
    path('', payment_home, name='payment_home'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Endpoints
    path('api/payment/process/', process_payment, name='process_payment'),
    path('api/payment/verify/<int:user_id>/<int:course_id>/', verify_course_access, name='verify_course_access'),
    path('api/payment/history/<int:user_id>/', get_user_payment_history, name='get_payment_history'),
    path('api/payment/methods/<int:user_id>/', get_saved_payment_methods, name='get_payment_methods'),
]