
from django.shortcuts import render, redirect
from django.views import View  # AJOUTEZ CET IMPORT
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from .forms import RegisterForm
from .models import User
from .serializers import UserSerializer

# ============ HTML VIEWS ============

# authentication/views.py - MODIFIEZ LoginView et RegisterView

class LoginView(View):
    template_name = 'authentication/login.html'
    
    def get(self, request):
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # Générer un token API
            tokens = user.generate_api_token()
            
            # Stocker le token dans la session (optionnel pour auth_server)
            request.session['auth_token'] = tokens['access_token']
            
            # REDIRIGEZ VERS UNE AUTRE URL
            return redirect(f'http://127.0.0.1:8000/api/auth-callback/?token={tokens["access_token"]}')
        else:
            messages.error(request, 'Identifiants incorrects')
        
        return render(request, self.template_name, {'form': form})

class RegisterView(View):
    template_name = 'authentication/register.html'
    
    def get(self, request):
        form = RegisterForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            
            # Générer un token API
            tokens = user.generate_api_token()
            
            # REDIRIGEZ VERS LA MÊME URL
            return redirect(f'http://127.0.0.1:8000/api/auth-callback/?token={tokens["access_token"]}')
        
        return render(request, self.template_name, {'form': form})
class LogoutView(View):
    def get(self, request):
        # Nettoyer la session
        if 'auth_token' in request.session:
            # Invalider le token dans la base de données
            token = request.session['auth_token']
            try:
                user = User.objects.get(api_token=token)
                user.api_token = None
                user.token_expiry = None
                user.refresh_token = None
                user.save()
            except User.DoesNotExist:
                pass
            
            del request.session['auth_token']
        
        # Déconnexion Django
        auth_logout(request)
        
        # Rediriger vers la page de login
        return redirect('login_html')

# ============ API VIEWS ============
# (Conservez vos vues API existantes ci-dessous)
# ...

# AJOUTEZ CES IMPORTS POUR LES VUES API
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import LoginSerializer, RegisterSerializer
# ============ API VIEWS ============

@method_decorator(csrf_exempt, name='dispatch')
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = user.generate_api_token()
            
            return Response({
                'success': True,
                'message': 'Inscription réussie',
                'user': UserSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = user.generate_api_token()
            
            # Optionnel: connecter l'utilisateur dans Django (pour admin)
            django_login(request, user)
            
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'user': UserSerializer(user).data,
                'tokens': tokens
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutAPIView(APIView):
    def post(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if token:
            try:
                user = User.objects.get(api_token=token)
                user.api_token = None
                user.token_expiry = None
                user.refresh_token = None
                user.save()
            except User.DoesNotExist:
                pass
        
        # Déconnecter de Django aussi
        django_logout(request)
        
        return Response({
            'success': True,
            'message': 'Déconnexion réussie'
        })

@method_decorator(csrf_exempt, name='dispatch')
class VerifyTokenAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({
                'success': False,
                'error': 'Token manquant'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(api_token=token)
            if user.is_token_valid():
                return Response({
                    'success': True,
                    'valid': True,
                    'user': UserSerializer(user).data
                })
            return Response({
                'success': True,
                'valid': False,
                'error': 'Token expiré'
            })
        except User.DoesNotExist:
            return Response({
                'success': True,
                'valid': False,
                'error': 'Token invalide'
            })

@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({
                'success': False,
                'error': 'Refresh token manquant'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(refresh_token=refresh_token)
            new_token = user.refresh_api_token()
            if new_token:
                return Response({
                    'success': True,
                    'access_token': new_token,
                    'refresh_token': user.refresh_token
                })
        except User.DoesNotExist:
            pass
        
        return Response({
            'success': False,
            'error': 'Refresh token invalide'
        }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class UserProfileAPIView(APIView):
    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if not token:
            return Response({
                'success': False,
                'error': 'Token manquant'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(api_token=token)
            if user.is_token_valid():
                return Response({
                    'success': True,
                    'user': UserSerializer(user).data
                })
        except User.DoesNotExist:
            pass
        
        return Response({
            'success': False,
            'error': 'Non authentifié'
        }, status=status.HTTP_401_UNAUTHORIZED)

@method_decorator(csrf_exempt, name='dispatch')
class CheckAuthAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Vérifie si l'utilisateur est authentifié (pour le serveur principal)"""
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if token:
            try:
                user = User.objects.get(api_token=token)
                if user.is_token_valid():
                    return Response({
                        'success': True,
                        'authenticated': True,
                        'user': UserSerializer(user).data
                    })
            except User.DoesNotExist:
                pass
        
        return Response({
            'success': True,
            'authenticated': False
        })


