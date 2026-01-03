#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# 🔥 PATCH CRITIQUE : Force pymysql à se faire passer pour mysqlclient 2.2.1
import pymysql
pymysql.version_info = (2, 2, 1, "final", 0)  # TRICHE 1
pymysql.install_as_MySQLdb()

# 🔥 PATCH MariaDB : Désactive la vérification de version MariaDB
import django
from django.db.backends.mysql.base import DatabaseWrapper

original_check = DatabaseWrapper.check_database_version_supported
def patched_check(self):
    try:
        return original_check(self)
    except Exception as e:
        if "MariaDB 10.6" in str(e):
            print("✅ MariaDB 10.4 accepté (patch appliqué)")
            return
        raise
DatabaseWrapper.check_database_version_supported = patched_check

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monprojet.settings')  # ⚠️ CHANGE ICI SEULEMENT
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()