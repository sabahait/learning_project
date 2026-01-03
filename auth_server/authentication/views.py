# authentication/views.py - VERSION CORRIGÉE
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
from .forms import RegisterForm
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import LoginSerializer, RegisterSerializer
from .models import User
from .serializers import UserSerializer
import json 

# ============ VUES HTML ============
# authentication/views.py - MODIFIEZ LoginAPIView
@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            # Récupérer l'utilisateur depuis les données validées
            user = serializer.validated_data['user']
            
            # Générer les tokens
            tokens = user.generate_api_token()
            
            # Optionnel: connecter l'utilisateur dans Django (pour admin)
            from django.contrib.auth import login as django_login
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
class RegisterView(View):
    """Page HTML d'inscription sur l'auth_server"""
    template_name = 'authentication/register.html'
    
    def get(self, request):
        form = RegisterForm()
        redirect_url = request.GET.get('redirect', '/')
        return render(request, self.template_name, {
            'form': form,
            'redirect_url': redirect_url
        })
    
    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            
            tokens = user.generate_api_token()
            
            # Récupérer l'URL de redirection
            redirect_url = request.GET.get('redirect', '/')
            
            # Construire l'URL de callback sur le main server
            callback_url = f"http://127.0.0.1:8000/auth/callback/"
            full_url = f"{callback_url}?token={tokens['access_token']}&redirect={redirect_url}"
            
            # Utiliser le même système que LoginView
            return render(request, 'authentication/redirect.html', {
                'redirect_url': full_url
            })
        
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
        from django.contrib.auth import logout as auth_logout
        auth_logout(request)
        
        # Rediriger vers la page de login
        return redirect('login_html')

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
            from django.contrib.auth import login as django_login
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
        from django.contrib.auth import logout as django_logout
        django_logout(request)
        
        return Response({
            'success': True,
            'message': 'Déconnexion réussie'
        })

@method_decorator(csrf_exempt, name='dispatch')
class VerifyTokenAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print(f"🔐 [VerifyTokenAPIView] Requête reçue")
        print(f"   Content-Type: {request.content_type}")
        print(f"   Données brutes: {request.body[:200]}...")
        
        # Essayer de récupérer le token de différentes manières
        token = None
        
        # 1. Depuis JSON
        try:
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
                token = data.get('token')
                print(f"   Token depuis JSON: {token[:30]}..." if token else "Non trouvé")
        except:
            pass
        
        # 2. Depuis form data
        if not token:
            token = request.POST.get('token')
            print(f"   Token depuis POST: {token[:30]}..." if token else "Non trouvé")
        
        # 3. Depuis query params
        if not token:
            token = request.GET.get('token')
            print(f"   Token depuis GET: {token[:30]}..." if token else "Non trouvé")
        
        if not token:
            print("❌ Token manquant dans la requête")
            return Response({
                'success': False,
                'valid': False,
                'error': 'Token manquant'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"✅ Token reçu: {token[:50]}...")
        
        try:
            user = User.objects.get(api_token=token)
            if user.is_token_valid():
                print(f"✅ Token valide pour: {user.username}")
                return Response({
                    'success': True,
                    'valid': True,
                    'user': UserSerializer(user).data
                })
            else:
                print("❌ Token expiré")
                return Response({
                    'success': True,
                    'valid': False,
                    'error': 'Token expiré'
                })
        except User.DoesNotExist:
            print("❌ Utilisateur non trouvé pour ce token")
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


# authentication/views.py - AJOUTEZ ces classes

@method_decorator(csrf_exempt, name='dispatch')
class UpdateProfileAPIView(APIView):
    """API pour mettre à jour le profil utilisateur"""
    def put(self, request):
        print("=" * 60)
        print("🔄 [UpdateProfileAPIView] DÉBUT")
        
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        print(f"🔑 Token reçu: {token[:50]}...")
        
        if not token:
            print("❌ Token manquant")
            return Response({
                'success': False,
                'error': 'Token manquant'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(api_token=token)
            print(f"👤 Utilisateur trouvé: {user.username} (ID: {user.id})")
            
            if not user.is_token_valid():
                print("❌ Token expiré")
                return Response({
                    'success': False,
                    'error': 'Token expiré'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Lire les données de la requête
            print(f"📊 Content-Type de la requête: {request.content_type}")
            
            # Essayer plusieurs méthodes pour obtenir les données
            data = {}
            
            if request.content_type == 'application/json':
                try:
                    body_bytes = request.body
                    print(f"📦 Body bytes: {len(body_bytes)} bytes")
                    
                    if body_bytes:
                        body_str = body_bytes.decode('utf-8')
                        print(f"📋 Body string: {body_str[:200]}...")  # Limiter l'affichage
                        
                        # IMPORTANT: Vérifier si le body n'est pas vide
                        if body_str.strip():
                            data = json.loads(body_str)
                            print(f"✅ JSON parsé avec succès")
                        else:
                            print("⚠️ Body string vide ou ne contient que des espaces")
                            return Response({
                                'success': False,
                                'error': 'Données JSON vides'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        print("⚠️ Body bytes vide")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur parsing JSON: {e}")
                    return Response({
                        'success': False,
                        'error': f'Format JSON invalide: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                except UnicodeDecodeError as e:
                    print(f"❌ Erreur décodage UTF-8: {e}")
                    return Response({
                        'success': False,
                        'error': f'Erreur de décodage UTF-8: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Pour form-data ou autre
                data = request.data
                print(f"📋 Données depuis request.data: {data}")
            
            print(f"📝 Données reçues pour mise à jour: {data}")
            
            if not data:
                print("❌ Aucune donnée reçue")
                return Response({
                    'success': False,
                    'error': 'Aucune donnée fournie pour la mise à jour'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ============ VALIDATION DES DONNÉES ============
            print("🔍 Validation des données...")
            
            # Champs autorisés à mettre à jour
            allowed_fields = [
                'first_name', 'last_name', 'email',
                'date_naissance', 'telephone', 'pays',
                'langue', 'bio', 'website', 'linkedin', 'github'
            ]
            
            # Vérifier les champs obligatoires pour l'email
            if 'email' in data:
                email = data['email']
                if not email or email.strip() == '':
                    print("❌ Email vide")
                    return Response({
                        'success': False,
                        'error': 'L\'email est obligatoire'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validation format email
                email = email.lower().strip()
                if '@' not in email or '.' not in email.split('@')[-1]:
                    print(f"❌ Email invalide: {email}")
                    return Response({
                        'success': False,
                        'error': 'Format d\'email invalide'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            updated_fields = []
            validation_errors = []
            
            for field in allowed_fields:
                if field in data and data[field] is not None:
                    # Nettoyer la valeur
                    if isinstance(data[field], str):
                        value = data[field].strip()
                    else:
                        value = data[field]
                    
                    old_value = getattr(user, field)
                    
                    # Si la valeur a changé
                    if str(old_value) != str(value):
                        # Validation spécifique pour chaque champ
                        if field == 'email':
                            # Vérifier si l'email n'est pas déjà utilisé
                            existing_user = User.objects.filter(email=value).exclude(pk=user.pk).first()
                            if existing_user:
                                print(f"❌ Email '{value}' déjà utilisé par {existing_user.username}")
                                validation_errors.append(f"L'email {value} est déjà utilisé")
                                continue
                        
                        elif field == 'telephone':
                            # Validation simple du téléphone
                            if value and not value.replace(' ', '').replace('+', '').replace('-', '').isdigit():
                                print(f"⚠️ Téléphone invalide: {value}")
                                validation_errors.append(f"Numéro de téléphone invalide: {value}")
                                continue
                        
                        setattr(user, field, value)
                        updated_fields.append(field)
                        print(f"📝 {field}: '{old_value}' → '{value}'")
            
            # Si des erreurs de validation
            if validation_errors:
                print(f"❌ Erreurs de validation: {validation_errors}")
                return Response({
                    'success': False,
                    'error': 'Erreurs de validation',
                    'details': validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if updated_fields:
                user.save()
                print(f"✅ Profil mis à jour: {', '.join(updated_fields)}")
                
                # Retourner les données utilisateur mises à jour
                user.refresh_from_db()
                user_data = UserSerializer(user).data
                
                print("🔄 [UpdateProfileAPIView] FIN")
                print("=" * 60)
                
                return Response({
                    'success': True,
                    'message': 'Profil mis à jour avec succès',
                    'user': user_data
                })
            else:
                print("ℹ️ Aucun champ modifié")
                return Response({
                    'success': True,
                    'message': 'Aucune modification détectée',
                    'user': UserSerializer(user).data
                })
            
        except User.DoesNotExist:
            print("❌ Utilisateur non trouvé pour ce token")
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"💥 Exception: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Erreur interne: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name='dispatch')
class UpdatePasswordAPIView(APIView):
    """API pour changer le mot de passe"""
    def post(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if not token:
            return Response({
                'success': False,
                'error': 'Token manquant'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(api_token=token)
            if not user.is_token_valid():
                return Response({
                    'success': False,
                    'error': 'Token expiré'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            # Validation
            if not all([current_password, new_password, confirm_password]):
                return Response({
                    'success': False,
                    'error': 'Tous les champs sont obligatoires'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier l'ancien mot de passe
            if not user.check_password(current_password):
                return Response({
                    'success': False,
                    'error': 'Mot de passe actuel incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier que les nouveaux mots de passe correspondent
            if new_password != confirm_password:
                return Response({
                    'success': False,
                    'error': 'Les nouveaux mots de passe ne correspondent pas'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier la force du mot de passe
            if len(new_password) < 8:
                return Response({
                    'success': False,
                    'error': 'Le mot de passe doit contenir au moins 8 caractères'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Changer le mot de passe
            user.set_password(new_password)
            user.save()
            
            # Régénérer le token après changement de mot de passe
            user.api_token = None
            user.token_expiry = None
            user.refresh_token = None
            user.save()
            
            # Recréer un token pour la session courante
            tokens = user.generate_api_token()
            
            return Response({
                'success': True,
                'message': 'Mot de passe changé avec succès',
                'tokens': tokens
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

# auth_server/authentication/views.py - MODIFIEZ UploadProfilePhotoAPIView

@method_decorator(csrf_exempt, name='dispatch')
class UploadProfilePhotoAPIView(APIView):
    """API pour uploader une photo de profil"""
    
    def post(self, request):
        print("=" * 60)
        print("🔄 [UploadProfilePhotoAPIView - AUTH SERVER] DÉBUT")
        
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if not token:
            print("❌ Token manquant")
            return Response({
                'success': False,
                'error': 'Token manquant'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(api_token=token)
            print(f"👤 Utilisateur trouvé: {user.username} (ID: {user.id})")
            
            if not user.is_token_valid():
                print("❌ Token expiré")
                return Response({
                    'success': False,
                    'error': 'Token expiré'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Vérifier s'il y a un fichier
            if 'photo' not in request.FILES:
                print("❌ Aucun fichier photo reçu")
                return Response({
                    'success': False,
                    'error': 'Aucune photo fournie'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            photo = request.FILES['photo']
            print(f"📁 Fichier reçu: {photo.name} ({photo.size} bytes, {photo.content_type})")
            
            # Vérifier le type de fichier
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if photo.content_type not in allowed_types:
                print(f"❌ Type non autorisé: {photo.content_type}")
                return Response({
                    'success': False,
                    'error': 'Type de fichier non autorisé. Utilisez JPG, PNG, GIF ou WebP'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier la taille (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                print(f"❌ Fichier trop grand: {photo.size} bytes")
                return Response({
                    'success': False,
                    'error': 'La photo est trop grande (max 5MB)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Supprimer l'ancienne photo si elle existe
            if user.photo_profil and user.photo_profil.name:
                try:
                    import os
                    old_path = user.photo_profil.path
                    print(f"🗑️ Suppression ancienne photo: {old_path}")
                    if os.path.isfile(old_path):
                        os.remove(old_path)
                        print("✅ Ancienne photo supprimée")
                except Exception as e:
                    print(f"⚠️ Erreur suppression ancienne photo: {e}")
            
            # Générer un nom de fichier unique
            import uuid
            import os
            
            # Obtenir l'extension
            ext = os.path.splitext(photo.name)[1]
            if not ext:
                ext = '.jpg'  # Extension par défaut
            
            # Nom de fichier unique
            filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}{ext}"
            
            # Sauvegarder la nouvelle photo
            user.photo_profil.save(filename, photo, save=True)
            user.save()
            
            # Construire l'URL CORRECTE
            # Les photos sont dans /media/profiles/ sur l'auth server
            photo_url = f"/media/profiles/{filename}"
            
            print(f"✅ Photo sauvegardée: {user.photo_profil.path}")
            print(f"📸 URL photo: {photo_url}")
            print(f"📸 URL complète: http://127.0.0.1:8001{photo_url}")
            
            print("🔄 [UploadProfilePhotoAPIView - AUTH SERVER] FIN")
            print("=" * 60)
            
            return Response({
                'success': True,
                'message': 'Photo de profil mise à jour',
                'photo_url': photo_url,
                'filename': filename
            })
            
        except User.DoesNotExist:
            print("❌ Utilisateur non trouvé pour ce token")
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"💥 Exception: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Erreur interne: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """API pour uploader une photo de profil"""
    def post(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if not token:
            return Response({
                'success': False,
                'error': 'Token manquant'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(api_token=token)
            if not user.is_token_valid():
                return Response({
                    'success': False,
                    'error': 'Token expiré'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Vérifier s'il y a un fichier
            if 'photo' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'Aucune photo fournie'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            photo = request.FILES['photo']
            
            # Vérifier le type de fichier
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if photo.content_type not in allowed_types:
                return Response({
                    'success': False,
                    'error': 'Type de fichier non autorisé. Utilisez JPG, PNG ou GIF'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier la taille (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                return Response({
                    'success': False,
                    'error': 'La photo est trop grande (max 5MB)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Supprimer l'ancienne photo si elle existe
            if user.photo_profil and user.photo_profil.name:
                try:
                    import os
                    if os.path.isfile(user.photo_profil.path):
                        os.remove(user.photo_profil.path)
                except:
                    pass
            
            # Sauvegarder la nouvelle photo
            user.photo_profil = photo
            user.save()
            
            return Response({
                'success': True,
                'message': 'Photo de profil mise à jour',
                'photo_url': user.photo_profil.url if user.photo_profil else None
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)