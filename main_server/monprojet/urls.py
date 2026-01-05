# mainserver/monprojet/urls.py - VERSION FINALE
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import json 
from pages.views import (
    home, login_view, register_view, logout_view,
    admin_courses, admin_users, administrateur_dashboard,
    dashboard, courses_available, profil, cours, historique,
    api_create_course, api_get_categories, api_get_courses,
    api_upload_file, api_update_course, api_delete_course,
    serve_course_image,proxy_profile_image,
    api_update_profile, api_update_password, api_upload_profile_photo,serve_course_pdf,api_get_my_courses
    ,api_my_courses,api_enroll_course,api_unenroll_course,api_admin_users,api_admin_stats,api_admin_recent_orders
    ,api_get_recommended_courses,recent_enrollments# <-- CES fonctions existent déjà
)

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    # Authentication
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Pages principales
    path('', home, name='home'),


    
     path('api/courses/recommended/', api_get_recommended_courses, name='api_recommended_courses'),
     path('api/enrollments/recent/', recent_enrollments, name='recent_enrollments'),
    # PAGES ADMINISTRATEUR
    path('administrateur/courses/', admin_courses, name='administrateur_courses'),
    path('administrateur/users/', admin_users, name='administrateur_users'),
    path('administrateur/dashboard/', administrateur_dashboard, name='administrateur_dashboard'),
     path('api/admin/stats/', api_admin_stats, name='api_admin_stats'),
    path('api/admin/recent-orders/', api_admin_recent_orders, name='api_admin_recent_orders'),

    # API ENDPOINTS POUR PROFIL (proxy vers auth server)
    path('api/profile/update/', api_update_profile, name='api_profile_update'),
    path('api/profile/password/', api_update_password, name='api_profile_password'),
    path('api/profile/photo/', api_upload_profile_photo, name='api_profile_photo'),
     path('media/profile_photos/<path:image_path>', proxy_profile_image, name='proxy_profile_image'),
     

    # API COURS
    path('api/courses/create/', api_create_course, name='api_create_course'),
    path('api/create-course/', api_create_course, name='api_create_course_alt'),
    path('api/courses/<int:course_id>/update/', api_update_course, name='api_update_course'),
    path('api/categories/', api_get_categories, name='api_get_categories'),
    path('api/courses/', api_get_courses, name='api_get_courses'),
    path('api/courses/<int:course_id>/delete/', api_delete_course, name='api_delete_course'),
    path('api/upload/', api_upload_file, name='api_upload_file'), 
    path('media/course_covers/<path:image_path>', serve_course_image, name='course_covers'),
    path('media/pdfs/<path:pdf_name>', serve_course_pdf, name='serve_course_pdf'),
    # urls.py - Ajoutez cette ligne dans urlpatterns
path('api/courses/<int:course_id>/unenroll/', api_unenroll_course, name='api_unenroll_course'),
    path('api/my-courses/', api_get_my_courses, name='api_get_my_courses'),
     path('api/my-courses/',api_my_courses, name='api_my_courses'),
     path('api/courses/<int:course_id>/enroll/',api_enroll_course, name='api_enroll_course'),
#path('api/courses/enroll/<int:course_id>/',api_enroll_course, name='api_enroll_course'),
    path('api/courses/unenroll/<int:course_id>/',api_unenroll_course, name='api_unenroll_course'),
   path('api/admin/users/', api_admin_users, name='api_admin_users'),
    
    # PAGES UTILISATEUR
    path('dashboard/', dashboard, name='utilisateur_dashboard'),
    path('courses/', courses_available, name='courses_available'),
    path('profil/', profil, name='profil'),
    path('cours/', cours, name='cours'),
    path('historique/', historique, name='historique'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)