# courses/permissions.py
from rest_framework import permissions

class IsAuthenticatedByJWT(permissions.BasePermission):
    """Permission qui vérifie l'authentification via JWT middleware"""
    
    def has_permission(self, request, view):
        # Le middleware a-t-il défini user_data ?
        return hasattr(request, 'user_data') and request.user_data

class IsAdminByJWT(permissions.BasePermission):
    """Permission pour les administrateurs seulement"""
    
    def has_permission(self, request, view):
        if hasattr(request, 'user_data') and request.user_data:
            user_type = request.user_data.get('user_type', '').lower()
            return user_type == 'admin'
        return False