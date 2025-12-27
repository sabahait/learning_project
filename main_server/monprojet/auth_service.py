# main_server/monprojet/auth_service.py

from functools import wraps
import requests
from django.conf import settings
from django.contrib import messages  # AJOUTEZ CET IMPORT
from django.shortcuts import redirect, render

class AuthService:
    @staticmethod
    def login(username, password):
        try:
            response = requests.post(
                f"{settings.AUTH_API_URL}login/",
                json={'username': username, 'password': password}
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    @staticmethod
    def register(user_data):
        try:
            response = requests.post(
                f"{settings.AUTH_API_URL}register/",
                json=user_data
            )
            return response.json() if response.status_code == 201 else None
        except:
            return None
    
    @staticmethod
    def verify_token(token):
        try:
            response = requests.post(
                f"{settings.AUTH_API_URL}verify/",
                json={'token': token}
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None

            
# AJOUTEZ CETTE FONCTION MANQUANTE
def login_required_api(view_func):
    """Décorateur pour protéger les vues avec l'API auth"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.session.get('auth_token')
        if not token:
            messages.error(request, 'Veuillez vous connecter pour accéder à cette page.')
            return redirect('login')
        
        result = AuthService.verify_token(token)
        if not result or not result.get('valid'):
            messages.error(request, 'Session expirée. Veuillez vous reconnecter.')
            # Nettoyer la session
            if 'auth_token' in request.session:
                del request.session['auth_token']
            if 'user_data' in request.session:
                del request.session['user_data']
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper