# pages/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from monprojet.auth_service import AuthService, login_required_api
from django.conf import settings
import requests

def home(request):
    return render(request, 'pages/home.html')

def login_view(request):
    """Redirige VERS auth_server pour le login"""
    auth_server_url = "http://127.0.0.1:8001/login/"  # Port 8001!
    return redirect(auth_server_url)

def register_view(request):
    """Redirige VERS auth_server pour l'inscription"""
    auth_server_url = "http://127.0.0.1:8001/register/"  # Port 8001!
    return redirect(auth_server_url)

def logout_view(request):
    """Logout - nettoie la session locale ET sur auth_server"""
    token = request.session.get('auth_token')
    
    if token:
        # Appeler l'API logout d'auth_server
        try:
            requests.post(
                f"{settings.AUTH_API_URL}logout/",
                headers={'Authorization': f'Bearer {token}'},
                timeout=3
            )
        except:
            pass
    
    # Nettoyer la session locale
    request.session.flush()
    messages.success(request, 'Déconnexion réussie')
    
    # Rediriger vers auth_server pour logout complet
    auth_server_logout = "http://127.0.0.1:8001/logout/"
    return redirect(auth_server_logout)

def auth_callback(request):
    """Gère le callback après authentification sur auth_server"""
    token = request.GET.get('token')
    
    print(f"Token reçu dans callback: {token}")  # Pour débogage
    
    if not token:
        messages.error(request, 'Token manquant')
        return redirect('home')
    
    # Vérifier le token avec auth_server
    try:
        response = requests.post(
            f"{settings.AUTH_API_URL}verify/",
            json={'token': token},
            timeout=3
        )
        
        print(f"Réponse de vérification: {response.status_code}")  # Pour débogage
        
        if response.status_code == 200:
            data = response.json()
            print(f"Données de vérification: {data}")  # Pour débogage
            
            if data.get('valid'):
                # Stocker le token dans la session
                user_data = data.get('user', {})
                request.session['auth_token'] = token
                request.session['user_data'] = user_data
                
                # Déterminer le type d'utilisateur pour la redirection
                user_type = user_data.get('user_type', 'etudiant')
                print(f"Type d'utilisateur détecté: {user_type}")  # Pour débogage
                
                messages.success(request, 'Connexion réussie !')
                
                # Redirection selon le type d'utilisateur
                if user_type == 'admin':
                    print("Redirection vers admin_dashboard")  # Pour débogage
                    return redirect('administrateur_dashboard')
                else:
                    print("Redirection vers utilisateur_dashboard")  # Pour débogage
                    return redirect('utilisateur_dashboard')
            else:
                messages.error(request, 'Token invalide ou expiré')
        else:
            messages.error(request, 'Erreur de vérification du token')
    
    except requests.RequestException as e:
        print(f"Erreur de vérification: {e}")
        messages.error(request, 'Impossible de vérifier le token')
    
    return redirect('home')


# ============ VUES PROTÉGÉES ============

@login_required_api
def admin_courses(request):
    return render(request, 'administrateur/admin_courses.html')
@login_required_api
def admin_users(request):
    return render(request, 'administrateur/admin_users.html')
    
@login_required_api
def admin_dashboard(request):
    return render(request, 'administrateur/admin_dashboard.html')


# ============================================
# VUES UTILISATEUR
# ============================================
@login_required_api
def dashboard(request):
    """Dashboard utilisateur"""
    user_data = request.session.get('user_data', {})
    
    # Données par défaut si pas de données utilisateur
    default_user = {
        'username': 'Utilisateur',
        'first_name': 'John',
        'last_name': 'Doe',
        'user_type': 'student',
        'is_premium': False
    }
    
    # Fusionner les données par défaut avec les données réelles
    user_info = {**default_user, **user_data}
    
    return render(request, 'utilisateurs/dashboard.html', {
        'user': user_info
    })
@login_required_api
def courses_available(request):
    user_data = request.session.get('user_data', {})
    default_user = {
        'username': 'Utilisateur',
        'first_name': 'John',
        'last_name': 'Doe',
        'user_type': 'student',
        'is_premium': False
    }
    user_info = {**default_user, **user_data}
    return render(request, 'utilisateurs/courses_available.html',{
        'user': user_info
    })
@login_required_api
def profil(request):
    user_data = request.session.get('user_data', {})
    default_user = {
        'username': 'Utilisateur',
        'first_name': 'John',
        'last_name': 'Doe',
        'user_type': 'student',
        'is_premium': False
    }
    user_info = {**default_user, **user_data}
    return render(request, 'utilisateurs/profile.html',{
        'user': user_info
    })
@login_required_api
def cours(request):
    user_data = request.session.get('user_data', {})

    default_user = {
        'username': 'Utilisateur',
        'first_name': 'John',
        'last_name': 'Doe',
        'user_type': 'student',
        'is_premium': False
    }
    user_info = {**default_user, **user_data}
    return render(request, 'utilisateurs/cours.html',{
        'user': user_info
    })
@login_required_api
def historique(request):
    user_data = request.session.get('user_data', {})
    default_user = {
        'username': 'Utilisateur',
        'first_name': 'John',
        'last_name': 'Doe',
        'user_type': 'student',
        'is_premium': False
    }
    user_info = {**default_user, **user_data}
    return render(request, 'utilisateurs/historique.html',{
        'user': user_info
    })