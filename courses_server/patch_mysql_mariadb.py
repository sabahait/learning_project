# courses_server/mysql_patch.py
import django
from django.db.backends.mysql.base import DatabaseWrapper

def patch_mysql():
    # Patch pour désactiver la vérification de version MariaDB
    original_check_database_version_supported = DatabaseWrapper.check_database_version_supported
    
    def patched_check_database_version_supported(self):
        try:
            return original_check_database_version_supported(self)
        except Exception:
            # Ignore l'erreur de version pour MariaDB 10.4
            return None
    
    DatabaseWrapper.check_database_version_supported = patched_check_database_version_supported

# Appeler le patch au démarrage
patch_mysql()