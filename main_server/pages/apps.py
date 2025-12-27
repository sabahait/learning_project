from django.apps import AppConfig

class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
    
    def ready(self):
        # Supprimez cette ligne ou créez le fichier signals.py
        # import pages.signals  # ← COMMENTEZ OU SUPPRIMEZ CETTE LIGNE
        pass