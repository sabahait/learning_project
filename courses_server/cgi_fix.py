# cgi_fix.py - Pour Python 3.14+
"""
Backport du module cgi pour Django sous Python 3.14.
À placer dans le même dossier que manage.py.
"""

import sys
import io

# Création d'un faux module cgi minimal
class Module:
    class FieldStorage:
        def __init__(self, *args, **kwargs):
            self.fp = io.BytesIO()
            self.list = []
            
        def getvalue(self, key, default=None):
            for k, v in self.list:
                if k == key:
                    return v
            return default

# Injecte le faux module dans sys.modules
sys.modules['cgi'] = sys.modules[__name__]