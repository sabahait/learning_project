# courses/apps.py
from django.apps import AppConfig

class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'  # Ceci doit être exactement 'courses'