# courses/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Créer le router
router = DefaultRouter()
router.register(r'courses', views.CourseViewSet)  # Assurez-vous que CourseViewSet existe
router.register(r'categories', views.CategoryViewSet)  # Assurez-vous que CategoryViewSet existe

urlpatterns = [
    # API REST (pour l'admin)
    path('api/', include(router.urls)),
    
    # APIs simples (pour le frontend)
    path('', views.get_courses, name='get_courses'),
    path('categories/', views.get_categories, name='get_categories'),
    path('health/', views.health_check, name='health_check'),
    path('pdf/', views.get_pdf_courses, name='get_pdf_courses'),
    path('video/', views.get_video_courses, name='get_video_courses'),
    
    # Pour compatibilité avec votre code existant
    path('api/courses/', views.get_courses, name='api_courses'),
    path('api/categories/', views.get_categories, name='api_categories'),
    path('api/create/', views.CourseViewSet.as_view({'post': 'create'}), name='create_course'),
]