# main_server/pages/views.py
from django.shortcuts import render, redirect
import re
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from monprojet.auth_service import AuthService as MainAuthService, login_required_api  # Renommer ici
from django.conf import settings
import requests
import json
from django.http import JsonResponse
from pages.services import AuthService, CoursesService
@csrf_exempt
def api_upload_file(request):
    """Upload un fichier - CSRF exempt car utilisée par API"""
    # Récupérer le token depuis l'en-tête Authorization
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        # Essayer depuis POST/GET
        token = request.POST.get('token') or request.GET.get('token')
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    # Vérifier le token
    is_valid, user_data = AuthService.verify_token(token)
    if not is_valid:
        print(f"❌ Token invalide pour upload: {token[:30]}...")
        return JsonResponse({'error': 'Invalid token'}, status=401)
    
    # Upload vers le serveur de cours
    try:
        file = request.FILES['file']
        print(f"📤 Upload fichier: {file.name} ({file.size} bytes)")
        
        files = {'file': (file.name, file, file.content_type)}
        
        response = requests.post(
            f"{settings.COURSES_SERVICE_URL}/api/upload/",
            files=files,
            headers={'Authorization': f'Bearer {token}'},
            timeout=30
        )
        
        print(f"📡 Réponse upload: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Upload réussi: {data.get('url', 'N/A')}")
            return JsonResponse(data)
        else:
            error_msg = f'Upload failed: {response.status_code}'
            print(f"❌ {error_msg}")
            return JsonResponse({'error': error_msg}, status=response.status_code)
            
    except Exception as e:
        print(f"💥 Exception upload: {e}")
        return JsonResponse({'error': str(e)}, status=500)
def home(request):
    return render(request, 'pages/home.html')

def auth_iframe(request):
    """Sert une page avec iframe pointant vers l'auth server"""
    return render(request, 'auth_iframe.html', {
        'auth_server_url': 'http://127.0.0.1:8001'
    })

# pages/views.py du main server - AMÉLIOREZ login_view
def login_view(request):
    """Gère la connexion directement dans le main server"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '/')
        
        # Valider les champs
        if not username or not password:
            messages.error(request, 'Veuillez remplir tous les champs')
            return render(request, 'authentication/login.html')
        
        # Appeler l'API de l'auth server
        auth_data = {
            'username': username,
            'password': password
        }
        
        try:
            response = requests.post(
                'http://127.0.0.1:8001/api/auth/login/',
                json=auth_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            print(f"📡 Réponse auth server: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Données reçues: {data.get('success')}")
                
                if data.get('success'):
                    # Stocker le token et les données utilisateur
                    token = data['tokens']['access_token']
                    user_data = data['user']
                    
                    request.session['auth_token'] = token
                    request.session['user_data'] = user_data
                    request.session.modified = True
                    
                    print(f"💾 Session créée pour: {user_data.get('username')}")
                    print(f"   is_superuser: {user_data.get('is_superuser')}")
                    
                    messages.success(request, 'Connexion réussie !')
                    
                    # Redirection basée sur is_superuser
                    if user_data.get('is_superuser', False):
                        return redirect('administrateur_dashboard')
                    else:
                        return redirect('utilisateur_dashboard')
                else:
                    error_msg = data.get('errors', {}).get('non_field_errors', ['Identifiants incorrects'])[0]
                    messages.error(request, error_msg)
            else:
                # Essayer de lire le message d'erreur
                try:
                    error_data = response.json()
                    error_msg = error_data.get('errors', {}).get('non_field_errors', ['Erreur serveur'])[0]
                except:
                    error_msg = f'Erreur serveur: {response.status_code}'
                
                messages.error(request, error_msg)
                print(f"❌ Erreur: {error_msg}")
                
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Serveur d\'authentification indisponible')
            print("❌ Connexion impossible à l'auth server")
        except Exception as e:
            messages.error(request, f'Erreur inattendue: {str(e)}')
            print(f"💥 Exception: {e}")
            import traceback
            traceback.print_exc()
    
    # GET request - afficher le formulaire
    return render(request, 'authentication/login.html')

def register_view(request):
    """Gère l'inscription directement dans le main server"""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        user_data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password1'),
            'password2': request.POST.get('password2'),
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', '')
        }
        
        try:
            # Appeler l'API register de l'auth server
            response = requests.post(
                'http://127.0.0.1:8001/api/auth/register/',
                json=user_data,
                timeout=5
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    # Connexion automatique après inscription
                    token = data['tokens']['access_token']
                    user_data = data['user']
                    
                    request.session['auth_token'] = token
                    request.session['user_data'] = user_data
                    
                    messages.success(request, 'Inscription réussie !')
                    return redirect('utilisateur_dashboard')
                else:
                    # Afficher les erreurs de validation
                    errors = data.get('errors', {})
                    for field, error_list in errors.items():
                        for error in error_list:
                            messages.error(request, f"{field}: {error}")
            else:
                messages.error(request, 'Erreur lors de l\'inscription')
                
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Serveur d\'authentification indisponible')
    
    # GET request - afficher le formulaire
    return render(request, 'authentication/register.html')
@csrf_exempt
def logout_view(request):
    """Déconnexion simple sur le main server"""
    # Nettoyer la session
    request.session.flush()
    
    # Ajouter un message
    from django.contrib import messages
    messages.success(request, 'Déconnexion réussie')
    
    # Rediriger vers la page de login
    return redirect('login')
# LIGNE 97-106 - MODIFIEZ auth_callback :

def auth_callback(request):
    """Gère le callback après authentification"""
    token = request.GET.get('token')
    redirect_url = request.GET.get('redirect', '/')
    
    print("=" * 60)
    print("🔐 AUTH_CALLBACK DÉBUT")
    print(f"Token reçu: {token[:30]}..." if token else "❌ Pas de token")
    print(f"Redirect URL: {redirect_url}")
    
    if not token:
        messages.error(request, 'Token manquant')
        return redirect('login')
    
    # Vérifier le token avec auth_server
    try:
        auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://127.0.0.1:8001')
        verify_url = f"{auth_service_url.rstrip('/')}/api/auth/verify/"
        
        print(f"🌐 URL de vérification: {verify_url}")
        
        response = requests.post(
            verify_url,
            json={'token': token},
            timeout=5
        )
        
        print(f"📡 Status: {response.status_code}")
        print(f"📦 Réponse: {response.text[:200]}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Données: {data}")
            
            if data.get('success') and data.get('valid'):
                user_data = data.get('user', {})
                
                # Stocker dans la session
                request.session['auth_token'] = token
                request.session['user_data'] = user_data
                request.session.modified = True
                
                print(f"💾 Session stockée:")
                print(f"   auth_token: {bool(request.session.get('auth_token'))}")
                print(f"   user_data: {user_data}")
                
                # IMPORTANT: Vérifier is_superuser
                is_superuser = user_data.get('is_superuser', False)
                is_admin = user_data.get('is_staff', False) or is_superuser
                
                print(f"👤 Détection admin:")
                print(f"   is_superuser: {is_superuser}")
                print(f"   is_staff: {user_data.get('is_staff', False)}")
                print(f"   user_type: {user_data.get('user_type', 'etudiant')}")
                
                messages.success(request, 'Connexion réussie !')
                
                # Redirection BASÉE SUR is_superuser
                if is_superuser or is_admin:
                    print("➡️  Redirection vers admin_dashboard (superuser)")
                    return redirect('administrateur_dashboard')
                else:
                    print("➡️  Redirection vers utilisateur_dashboard (étudiant)")
                    return redirect('utilisateur_dashboard')
            else:
                error_msg = data.get('error', 'Token invalide')
                print(f"❌ Échec: {error_msg}")
                messages.error(request, f'Token invalide: {error_msg}')
        else:
            print(f"⚠️  Erreur HTTP {response.status_code}")
            messages.error(request, f'Erreur serveur: {response.status_code}')
    
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        messages.error(request, 'Serveur d\'authentification indisponible')
        
    except Exception as e:
        print(f"💥 Erreur: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Erreur inattendue')
    
    print("➡️  Redirection vers home (échec)")
    print("=" * 60)
    return redirect('home')
@csrf_exempt
@login_required_api
def admin_courses(request):
    # S'assurer que le token est dans la session
    if not request.session.get('auth_token') and hasattr(request, 'auth_token'):
        request.session['auth_token'] = request.auth_token
    
    # S'assurer que les données utilisateur sont dans la session
    if not request.session.get('user_data') and hasattr(request, 'user_data'):
        request.session['user_data'] = request.user_data
    
    context = {
        'auth_service_url': settings.AUTH_SERVICE_URL,
        'courses_service_url': settings.COURSES_SERVICE_URL,
        'user': request.user_data if hasattr(request, 'user_data') else {},
        'auth_token': request.session.get('auth_token', ''),
    }
    
    # Debug: vérifier ce qui est passé au template
    print(f"🔑 admin_courses - Token dans session: {bool(request.session.get('auth_token'))}")
    print(f"👤 admin_courses - User data: {request.session.get('user_data', {})}")
    
    return render(request, 'administrateur/admin_courses.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def api_get_courses(request):
    """API endpoint pour récupérer les cours"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        token = request.GET.get('token') or request.session.get('auth_token')
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Vérifier le token
    is_valid, user_data = AuthService.verify_token(token)
    if not is_valid:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    
    try:
        # Récupérer les cours depuis le serveur de cours
        courses_service_url = settings.COURSES_SERVICE_URL.rstrip('/')
        response = requests.get(
            f"{courses_service_url}/api/courses/",
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            courses_data = response.json()
            print(f"✅ Données reçues du serveur de cours: {type(courses_data)}")
            
            # Normaliser la structure des données
            normalized_courses = []
            
            if isinstance(courses_data, list):
                # Si c'est une liste directe
                for course in courses_data:
                    normalized_courses.append(normalize_course_data(course))
            elif isinstance(courses_data, dict) and 'courses' in courses_data:
                # Si c'est un dict avec clé 'courses'
                for course in courses_data['courses']:
                    normalized_courses.append(normalize_course_data(course))
            elif isinstance(courses_data, dict) and 'results' in courses_data:
                # Si c'est un dict avec pagination
                for course in courses_data['results']:
                    normalized_courses.append(normalize_course_data(course))
            else:
                # Autre structure
                print(f"⚠️ Structure inattendue, tentative de normalisation")
                if isinstance(courses_data, dict):
                    normalized_courses.append(normalize_course_data(courses_data))
            
            print(f"✅ {len(normalized_courses)} cours normalisés")
            
            # Obtenir les détails des fichiers pour chaque cours
            courses_with_details = []
            for course in normalized_courses:
                try:
                    # Récupérer les détails du cours (y compris les fichiers)
                    detail_response = requests.get(
                        f"{courses_service_url}/api/courses/{course['id']}/",
                        headers={'Authorization': f'Bearer {token}'},
                        timeout=5
                    )
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        # Fusionner les données de base avec les détails
                        merged_course = {**course, **detail_data}
                        courses_with_details.append(merged_course)
                    else:
                        courses_with_details.append(course)
                        
                except Exception as e:
                    print(f"⚠️ Erreur récupération détails cours {course.get('id')}: {e}")
                    courses_with_details.append(course)
            
            return JsonResponse({'courses': courses_with_details}, safe=False)
        else:
            # En cas d'erreur, retourner des données de test pour debug
            print(f"⚠️ Erreur serveur cours: {response.status_code}")
            test_courses = [
                {
                    'id': 1,
                    'title': 'Introduction à Python',
                    'description': 'Apprenez les bases de Python',
                    'price': 29.99,
                    'category': {'id': 1, 'name': 'Programmation'},
                    'cover_photo': '/static/images/default-course.jpg',
                    'document_url': '#',
                    'document_file': '#',
                    'pages': 45,
                    'level': 'beginner',
                    'lesson_type': 'document',
                    'instructor_name': 'Admin',
                    'created_at': '2024-01-15'
                },
                {
                    'id': 2,
                    'title': 'HTML & CSS',
                    'description': 'Cours complet de développement web',
                    'price': 39.99,
                    'category': {'id': 2, 'name': 'Développement Web'},
                    'cover_photo': '/static/images/default-course.jpg',
                    'preview_video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'duration_hours': 3.5,
                    'level': 'beginner',
                    'lesson_type': 'video',
                    'instructor_name': 'Admin',
                    'created_at': '2024-01-20'
                }
            ]
            return JsonResponse({'courses': test_courses}, safe=False)
            
    except Exception as e:
        print(f"💥 Exception dans api_get_courses: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

def normalize_course_data(course):
    """Normalise les données d'un cours pour avoir une structure cohérente"""
    if not isinstance(course, dict):
        return {'id': 0, 'title': 'Cours inconnu'}
    
    # Extraire les champs de base
    normalized = {
        'id': course.get('id', 0),
        'title': course.get('title', 'Sans titre'),
        'description': course.get('description', ''),
        'short_description': course.get('short_description', course.get('description', '')[:200]),
        'price': float(course.get('price', 0)) if course.get('price') else 0,
        'category': course.get('category', {'id': 1, 'name': 'Non catégorisé'}),
        'level': course.get('level', 'beginner'),
        'instructor_name': course.get('instructor_name') or course.get('instructor', {}).get('username', 'Admin'),
        'created_at': course.get('created_at', ''),
        'status': course.get('status', 'published'),
    }
    
    # ========== CORRECTION IMPORTANTE POUR LES IMAGES ==========
    # Si cover_photo existe, ajouter l'URL complète du serveur de cours
    cover_photo = course.get('cover_photo')
    if cover_photo and cover_photo not in ['null', 'None', '']:
        # Si c'est déjà une URL complète, la garder
        if cover_photo.startswith('http'):
            normalized['cover_photo'] = cover_photo
        # Si c'est un chemin Django, ajouter l'URL du serveur de cours
        elif cover_photo.startswith('/media/'):
            normalized['cover_photo'] = f'http://127.0.0.1:8002{cover_photo}'
        # Si c'est juste un nom de fichier
        else:
            # Extraire le nom de fichier
            filename = cover_photo
            if '/' in cover_photo:
                filename = cover_photo.split('/')[-1]
            normalized['cover_photo'] = f'http://127.0.0.1:8002/media/course_covers/{filename}'
    else:
        # Image par défaut sur le main server
        normalized['cover_photo'] = '/static/images/default-course.jpg'
    
    # Même logique pour thumbnail
    thumbnail = course.get('thumbnail')
    if thumbnail and thumbnail not in ['null', 'None', '']:
        if thumbnail.startswith('http'):
            normalized['thumbnail'] = thumbnail
        elif thumbnail.startswith('/media/'):
            normalized['thumbnail'] = f'http://127.0.0.1:8002{thumbnail}'
        else:
            filename = thumbnail.split('/')[-1] if '/' in thumbnail else thumbnail
            normalized['thumbnail'] = f'http://127.0.0.1:8002/media/course_thumbnails/{filename}'
    
    # Ajouter les champs spécifiques si disponibles
    if 'document_file' in course:
        doc_file = course['document_file']
        if doc_file and doc_file not in ['null', 'None', '']:
            if doc_file.startswith('/media/'):
                normalized['document_file'] = f'http://127.0.0.1:8002{doc_file}'
            else:
                normalized['document_file'] = doc_file
    
    if 'document_url' in course:
        normalized['document_url'] = course['document_url']
    
    if 'preview_video_url' in course:
        normalized['preview_video_url'] = course['preview_video_url']
    
    if 'duration_hours' in course:
        normalized['duration_hours'] = course['duration_hours']
    
    if 'pages' in course:
        normalized['pages'] = course['pages']
    
    return normalized
@csrf_exempt
@require_http_methods(["POST"])
def api_create_course(request):
    """API endpoint pour créer un cours"""
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        return JsonResponse({'error': 'Authorization header missing or invalid'}, status=401)
    
    print(f"🔐 Création cours - Token reçu: {token[:30]}...")
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        # Vérifier si c'est du JSON ou du FormData
        content_type = request.headers.get('Content-Type', '')
        
        if 'multipart/form-data' in content_type:
            # Traitement FormData (avec fichiers)
            print("📦 Données reçues en FormData")
            
            # Récupérer les données du formulaire
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')
            price = float(request.POST.get('price', 0))
            category_id = int(request.POST.get('category_id', 1))
            pages = int(request.POST.get('pages', 0))
            level = request.POST.get('level', 'beginner')
            short_description = request.POST.get('short_description', description[:200] if description else '')
            
            # Récupérer les fichiers
            cover_photo = request.FILES.get('cover_photo')
            document_file = request.FILES.get('document_file')
            
            # Vérifier que l'utilisateur est authentifié
            is_valid, user_data = AuthService.verify_token(token)
            print(f"✅ Token valide: {is_valid}, User type: {user_data.get('user_type') if user_data else 'N/A'}")
            
            if not is_valid:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            # Vérifier que l'utilisateur est administrateur
            if user_data.get('user_type', '').lower() != 'admin':
                return JsonResponse({'error': 'Unauthorized - Admin only'}, status=403)
            
            # Préparer les données pour le serveur de cours
            course_type = 'paid' if price > 0 else 'free'
            
            course_data = {
                'title': title,
                'description': description,
                'short_description': short_description,
                'course_type': course_type,
                'level': level,
                'price': price,
                'duration_hours': 0,
                'language': 'Français',
                'category_id': category_id,
                'instructor_id': user_data.get('id'),
                'instructor_name': user_data.get('username', 'Admin'),
                'objectives': request.POST.get('objectives', 'Apprentissage via document PDF'),
                'prerequisites': request.POST.get('prerequisites', 'Aucun'),
                'target_audience': request.POST.get('target_audience', 'Tous niveaux'),
                'tags': request.POST.get('tags', 'pdf,document'),
                'pages': pages,
                'status': 'published',
            }
            
            print(f"📤 Envoi données au serveur cours: {json.dumps(course_data, indent=2)}")
            
            # Appeler le service de cours avec les fichiers
            success, response = CoursesService.create_course_with_files(course_data, cover_photo, document_file, token)
            
            if success:
                print(f"✅ Cours créé avec succès")
                return JsonResponse({'success': True, 'course': response}, status=201)
            else:
                print(f"❌ Erreur création cours: {response}")
                return JsonResponse({'error': response}, status=400)
                
        else:
            # Traitement JSON (sans fichiers)
            data = json.loads(request.body)
            print(f"📦 Données cours reçues (JSON): {json.dumps(data, indent=2)}")
            
            # Vérifier que l'utilisateur est authentifié
            is_valid, user_data = AuthService.verify_token(token)
            print(f"✅ Token valide: {is_valid}, User type: {user_data.get('user_type') if user_data else 'N/A'}")
            
            if not is_valid:
                return JsonResponse({'error': 'Invalid token'}, status=401)
            
            # Vérifier que l'utilisateur est administrateur
            if user_data.get('user_type', '').lower() != 'admin':
                return JsonResponse({'error': 'Unauthorized - Admin only'}, status=403)
            
            # Préparer les données pour le serveur de cours
            course_type = 'paid' if float(data.get('price', 0)) > 0 else 'free'
            
            course_data = {
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'short_description': data.get('short_description', data.get('description', '')[:200]),
                'course_type': course_type,
                'level': data.get('level', 'beginner'),
                'price': float(data.get('price', 0)),
                'duration_hours': float(data.get('duration_hours', 0)),
                'language': data.get('language', 'Français'),
                'category_id': int(data.get('category_id', 1)),
                'instructor_id': user_data.get('id'),
                'instructor_name': user_data.get('username', 'Admin'),
                'cover_photo': data.get('cover_photo', ''),
                'preview_video_url': data.get('preview_video_url', ''),
                'objectives': data.get('objectives', ''),
                'prerequisites': data.get('prerequisites', ''),
                'target_audience': data.get('target_audience', ''),
                'tags': data.get('tags', ''),
                'pages': int(data.get('pages', 0)),
                'status': 'published',
            }
            
            print(f"📤 Envoi données au serveur cours: {json.dumps(course_data, indent=2)}")
            
            # Appeler le service de cours
            success, response = CoursesService.create_course(course_data, token)
            
            if success:
                print(f"✅ Cours créé avec succès")
                return JsonResponse({'success': True, 'course': response}, status=201)
            else:
                print(f"❌ Erreur création cours: {response}")
                return JsonResponse({'error': response}, status=400)
            
    except json.JSONDecodeError:
        print("❌ JSON invalide")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"💥 Exception création cours: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

# AJOUTEZ cette vue pour obtenir les catégories
@csrf_exempt
@require_http_methods(["GET"])
def api_get_categories(request):
    """API endpoint pour récupérer les catégories"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Vérifier le token
    is_valid, user_data = AuthService.verify_token(token)
    if not is_valid:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    
    try:
        # Utiliser le service pour récupérer les catégories
        categories = CoursesService.get_categories(token)
        
        # Si pas de catégories, retourner des catégories par défaut
        if not categories:
            categories = [
                {'id': 1, 'name': 'Développement Web'},
                {'id': 2, 'name': 'Data Science'},
                {'id': 3, 'name': 'Mobile Development'},
                {'id': 4, 'name': 'Design UI/UX'},
                {'id': 5, 'name': 'Business'},
                {'id': 6, 'name': 'Marketing'},
            ]
        
        return JsonResponse({'categories': categories})
            
    except Exception as e:
        print(f"Exception dans api_get_categories: {str(e)}")
        # Retourner des catégories par défaut en cas d'erreur
        default_categories = [
            {'id': 1, 'name': 'Développement Web'},
            {'id': 2, 'name': 'Data Science'},
            {'id': 3, 'name': 'Design'},
            {'id': 4, 'name': 'Business'},
        ]
        return JsonResponse({'categories': default_categories})
@csrf_exempt
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
    
    # Debug
    print(f"📊 Dashboard - Données utilisateur: {user_data}")
    
    # Vérifier si c'est un admin
    is_admin = user_data.get('is_superuser', False) or user_data.get('is_staff', False)
    
    # Si c'est un admin et n'est pas sur le dashboard admin, suggérer redirection
    if is_admin and not request.path.startswith('/administrateur/'):
        print(f"⚠️  Admin détecté sur dashboard utilisateur, suggérer admin_dashboard")
    
    return render(request, 'utilisateurs/dashboard.html', {
        'user': user_data,
        'is_admin': is_admin
    })

    
# main_server/pages/views.py - MODIFIEZ courses_available

# main_server/pages/views.py - MODIFIEZ la fonction courses_available

# Dans views.py - MODIFIEZ la fonction courses_available

@login_required_api
def courses_available(request):
    user_data = request.session.get('user_data', {})
    
    # Récupérer le token pour les appels API
    auth_token = request.session.get('auth_token', '')
    
    print(f"🔑 courses_available - Token: {auth_token[:30] if auth_token else 'N/A'}...")
    print(f"👤 User: {user_data.get('username', 'N/A')}")
    
    courses_list = []
    
    if auth_token:
        try:
            # Utiliser get_all_courses qui existe déjà
            print("🔄 Tentative récupération cours via CoursesService.get_all_courses...")
            courses_data = CoursesService.get_all_courses(auth_token)
            
            if courses_data:
                print(f"✅ {len(courses_data)} cours récupérés depuis le serveur de cours")
                
                # Normaliser les données des cours
                for course in courses_data:
                    normalized_course = normalize_course_data(course)
                    courses_list.append(normalized_course)
                    
                print(f"✅ {len(courses_list)} cours normalisés pour affichage")
            else:
                print(f"⚠️ Aucun cours récupéré ou liste vide")
                # Données de test en cas d'erreur
                courses_list = get_test_courses()
                
        except Exception as e:
            print(f"💥 Exception récupération cours: {e}")
            import traceback
            traceback.print_exc()
            courses_list = get_test_courses()
    else:
        print("⚠️ Pas de token, utilisation données test")
        courses_list = get_test_courses()
    
    # Données utilisateur
    user_info = {
        'username': user_data.get('username', 'Utilisateur'),
        'first_name': user_data.get('first_name', 'John'),
        'last_name': user_data.get('last_name', 'Doe'),
        'user_type': user_data.get('user_type', 'student'),
        'is_premium': False,
    }
    
    # Préparer le contexte
    context = {
        'user': user_info,
        'auth_token': auth_token,
        'courses_data': json.dumps(courses_list),
        'courses_count': len(courses_list),
        'courses_service_url': settings.COURSES_SERVICE_URL,
    }
    
    return render(request, 'utilisateurs/courses_available.html', context)

def get_test_courses():
    """Retourne des cours de test pour debug"""
    return [
        {
            'id': 1,
            'title': 'Introduction à Python',
            'description': 'Apprenez les bases de la programmation avec Python',
            'short_description': 'Cours débutant Python',
            'price': 0.00,
            'course_type': 'free',
            'level': 'beginner',
            'duration_hours': 10,
            'pages': 50,
            'media_type': 'pdf',
            'category': {'id': 1, 'name': 'Développement'},
            'instructor_name': 'Admin',
            'cover_photo': '/static/images/default-course.jpg',
            'total_students': 100,
            'language': 'Français',
            'created_at': '2024-01-01',
            'is_featured': True,
            'certificate_available': True
        },
        {
            'id': 2,
            'title': 'Développement Web Avancé',
            'description': 'Maîtrisez le développement web moderne',
            'short_description': 'Cours avancé développement web',
            'price': 99.99,
            'course_type': 'paid',
            'level': 'advanced',
            'duration_hours': 40,
            'pages': 0,
            'media_type': 'video',
            'category': {'id': 1, 'name': 'Développement Web'},
            'instructor_name': 'Expert',
            'cover_photo': '/static/images/default-course.jpg',
            'total_students': 50,
            'language': 'Français',
            'created_at': '2024-01-15',
            'is_featured': False,
            'certificate_available': True
        }
    ]

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
@login_required_api
# ... (le code précédent reste inchangé)

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
    
    # Récupérer les cours inscrits depuis la session
    user_enrollments = []
    enrollments = request.session.get('enrollments', [])
    if user_data.get('id'):
        user_id = user_data.get('id')
        user_enrollments = [
            e for e in enrollments 
            if e.get('user_id') == user_id
        ]
    
    context = {
        'user': user_info,
        'auth_token': request.session.get('auth_token', ''),
        'enrollments_count': len(user_enrollments),
        'courses_service_url': settings.COURSES_SERVICE_URL,
    }
    
    return render(request, 'utilisateurs/cours.html', context)

# CORRECTION : Cette fonction doit être indentée correctement
@csrf_exempt
@require_http_methods(["DELETE"])
def api_unenroll_course(request, course_id):
    """API endpoint pour retirer un cours des cours sauvegardés"""
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.session.get('auth_token')
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Vérifier le token
    is_valid, user_data = AuthService.verify_token(token)
    if not is_valid:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    
    user_id = user_data.get('id')
    
    # Retirer de la session
    enrollments = request.session.get('enrollments', [])
    request.session['enrollments'] = [
        e for e in enrollments 
        if not (e.get('user_id') == user_id and e.get('course_id') == course_id)
    ]
    
    # Mettre à jour les cours dans la session
    if 'my_courses' in request.session:
        my_courses = request.session['my_courses']
        if str(course_id) in my_courses:
            del my_courses[str(course_id)]
            request.session['my_courses'] = my_courses
    
    request.session.modified = True
    
    print(f"✅ Cours {course_id} retiré pour utilisateur {user_id}")
    
    return JsonResponse({
        'success': True,
        'message': 'Cours retiré de votre liste'
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

# ... (le reste du code reste inchangé)

@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_course(request, course_id):
    """API endpoint pour supprimer un cours"""
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.session.get('auth_token')
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Vérifier le token
    is_valid, user_data = AuthService.verify_token(token)
    if not is_valid:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    
    # Vérifier que l'utilisateur est administrateur
    if user_data.get('user_type', '').lower() != 'admin':
        return JsonResponse({'error': 'Unauthorized - Admin only'}, status=403)
    
    try:
        # Appeler le service de cours pour supprimer
        success, message = CoursesService.delete_course(course_id, token)
        
        if success:
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'error': message}, status=400)
            
    except Exception as e:
        print(f"💥 Exception suppression cours: {e}")
        return JsonResponse({'error': str(e)}, status=500)




@csrf_exempt
@require_http_methods(["PUT", "PATCH", "POST"])
def api_update_course(request, course_id):
    """API endpoint pour modifier un cours - VERSION CORRIGÉE"""
    print(f"🔄 Modification cours ID: {course_id}")
    print(f"📊 Méthode HTTP: {request.method}")
    print(f"📊 Content-Type: {request.content_type}")
    
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        # Vérifier l'authentification
        is_valid, user_data = AuthService.verify_token(token)
        print(f"✅ Token valide: {is_valid}, User ID: {user_data.get('id') if user_data else 'N/A'}")
        
        if not is_valid:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        if user_data.get('user_type', '').lower() != 'admin':
            return JsonResponse({'error': 'Unauthorized - Admin only'}, status=403)
        
        # IMPORTANT: Récupérer l'ID de l'utilisateur
        instructor_id = user_data.get('id')
        print(f"👤 Instructor ID: {instructor_id}")
        
        # Si pas d'ID, utiliser une valeur par défaut
        if not instructor_id:
            instructor_id = 1  # Admin par défaut
            print(f"⚠️ Utilisation ID par défaut: {instructor_id}")
        
        # ========== TRAITEMENT DES DONNÉES ==========
        
        # 1. Vérifier si c'est du FormData
        if 'multipart/form-data' in request.content_type:
            print("🔄 Traitement FormData (PUT/PATCH)")
            
            # DEBUG: Voir ce que contient la requête
            print(f"📊 POST keys: {list(request.POST.keys())}")
            print(f"📊 FILES keys: {list(request.FILES.keys())}")
            print(f"📊 Body size: {len(request.body) if request.body else 0} bytes")
            
            # ===== FONCTION POUR PARSER MANUELLEMENT LE FORMDATA =====
            def parse_form_data_from_body(body):
                """Parse manuellement le FormData depuis le body"""
                try:
                    # Décoder le body
                    body_text = body.decode('utf-8', errors='ignore')
                    
                    # Extraire les boundary
                    boundary_match = re.search(r'boundary=([^\r\n]+)', request.content_type)
                    if not boundary_match:
                        print("❌ Pas de boundary trouvé")
                        return {}
                    
                    boundary = '--' + boundary_match.group(1)
                    parts = body_text.split(boundary)
                    
                    data = {}
                    
                    for part in parts:
                        if 'Content-Disposition: form-data;' in part:
                            # Chercher le nom du champ
                            name_match = re.search(r'name="([^"]+)"', part)
                            if name_match:
                                field_name = name_match.group(1)
                                
                                # Chercher la valeur (après deux retours à la ligne)
                                value_match = re.search(r'\r\n\r\n(.*?)\r\n', part, re.DOTALL)
                                if value_match:
                                    field_value = value_match.group(1).strip()
                                    data[field_name] = field_value
                    
                    print(f"📋 Données parsées manuellement: {list(data.keys())}")
                    return data
                
                except Exception as e:
                    print(f"⚠️ Erreur parsing manuel: {e}")
                    return {}
            
            # ===== TENTER DE RÉCUPÉRER LES DONNÉES =====
            
            # Essayer plusieurs méthodes pour récupérer les données
            
            # Méthode 1: Utiliser request.POST (fonctionne avec POST mais pas toujours avec PUT)
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            
            # Méthode 2: Si vide, essayer de parser le body manuellement
            if not title or not description:
                print("⚠️ Données manquantes dans request.POST, parsing manuel...")
                parsed_data = parse_form_data_from_body(request.body)
                
                if not title and 'title' in parsed_data:
                    title = parsed_data['title'].strip()
                
                if not description and 'description' in parsed_data:
                    description = parsed_data['description'].strip()
                
                if not title and 'title' in parsed_data:
                    title = parsed_data['title'].strip()
            
            # Méthode 3: Si toujours vide, essayer d'accéder via request.body directement
            if not title:
                try:
                    # Essayer de trouver dans le body texte
                    body_text = request.body.decode('utf-8', errors='ignore')
                    
                    # Recherche simple
                    import re
                    title_match = re.search(r'name="title"[^\r\n]*(?:\r\n)+([^\r\n]+)', body_text)
                    if title_match:
                        title = title_match.group(1).strip()
                        print(f"🔍 Title extrait via regex: '{title}'")
                    
                    desc_match = re.search(r'name="description"[^\r\n]*(?:\r\n)+([^\r\n]+)', body_text, re.DOTALL)
                    if desc_match:
                        description = desc_match.group(1).strip()
                        print(f"🔍 Description extraite via regex: '{description[:50]}...'")
                        
                except Exception as e:
                    print(f"⚠️ Erreur extraction regex: {e}")
            
            # ===== VÉRIFICATION DES DONNÉES OBLIGATOIRES =====
            
            print(f"📋 Résultat extraction:")
            print(f"   Title: '{title if title else 'VIDE'}'")
            print(f"   Description: '{description[:50] if description else 'VIDE'}...'")
            
            # Si toujours vide, erreur
            if not title:
                print("❌ ERROR: Title est vide après toutes les tentatives!")
                return JsonResponse({
                    'error': 'Le titre est obligatoire',
                    'details': 'Champ "title" non trouvé dans la requête FormData'
                }, status=400)
            
            if not description:
                print("❌ ERROR: Description est vide après toutes les tentatives!")
                return JsonResponse({
                    'error': 'La description est obligatoire',
                    'details': 'Champ "description" non trouvé dans la requête FormData'
                }, status=400)
            
            # ===== RÉCUPÉRATION DES AUTRES CHAMPS =====
            
            # Utiliser request.POST ou le parsing manuel
            short_description = request.POST.get('short_description', '').strip()
            if not short_description:
                # Essayer parsed_data
                if 'parsed_data' in locals() and 'short_description' in parsed_data:
                    short_description = parsed_data['short_description'].strip()
            
            # Si toujours vide, utiliser description
            if not short_description and description:
                short_description = description[:200]
            
            # Récupérer les autres champs
            price = request.POST.get('price', '0')
            if not price or price == '0':
                if 'parsed_data' in locals() and 'price' in parsed_data:
                    price = parsed_data['price'].strip() or '0'
            
            category_id = request.POST.get('category_id', '1')
            if not category_id or category_id == '1':
                if 'parsed_data' in locals() and 'category_id' in parsed_data:
                    category_id = parsed_data['category_id'].strip() or '1'
            
            pages = request.POST.get('pages', '0')
            if not pages or pages == '0':
                if 'parsed_data' in locals() and 'pages' in parsed_data:
                    pages = parsed_data['pages'].strip() or '0'
            
            level = request.POST.get('level', 'beginner')
            if not level or level == 'beginner':
                if 'parsed_data' in locals() and 'level' in parsed_data:
                    level = parsed_data['level'].strip() or 'beginner'
            
            author = request.POST.get('instructor_name', user_data.get('username', 'Admin'))
            if not author or author == 'Admin':
                if 'parsed_data' in locals() and 'instructor_name' in parsed_data:
                    author = parsed_data['instructor_name'].strip() or user_data.get('username', 'Admin')
            
            # ===== PRÉPARATION DES DONNÉES =====
            
            try:
                price_float = float(price) if price and price != '' else 0.0
            except:
                price_float = 0.0
            
            try:
                category_id_int = int(category_id) if category_id and category_id != '' else 1
            except:
                category_id_int = 1
            
            try:
                pages_int = int(pages) if pages and pages != '' else 0
            except:
                pages_int = 0
            
            course_data = {
                'title': title,
                'description': description,
                'short_description': short_description,
                'price': price_float,
                'category_id': category_id_int,
                'pages': pages_int,
                'level': level,
                'course_type': 'paid' if price_float > 0 else 'free',
                'instructor_id': instructor_id,
                'instructor_name': author,
                'status': 'published',
            }
            
            print(f"📤 Données préparées pour service de cours:")
            for key, value in course_data.items():
                print(f"   {key}: {value}")
            
            # Récupérer les fichiers
            cover_photo = request.FILES.get('cover_photo')
            document_file = request.FILES.get('document_file')
            
            print(f"📁 Fichiers reçus: Cover={cover_photo is not None}, PDF={document_file is not None}")
            
            # ===== APPEL AU SERVICE =====
            
            # Utiliser le service existant
            success, response = CoursesService.update_course_with_files(
                course_id, course_data, cover_photo, document_file, token
            )
            
            if success:
                print(f"✅ Cours modifié avec succès")
                return JsonResponse({'success': True, 'course': response})
            else:
                print(f"❌ Erreur modification cours: {response}")
                return JsonResponse({'error': response}, status=400)
            
        else:
            # ===== TRAITEMENT JSON =====
            print("🔄 Traitement JSON")
            
            # URL du service de cours
            courses_service_url = settings.COURSES_SERVICE_URL.rstrip('/')
            url = f"{courses_service_url}/api/courses/{course_id}/"
            
            # Préparer les headers
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': request.headers.get('Content-Type', 'application/json'),
            }
            
            print(f"📤 Envoi à: {url}")
            
            # Envoyer directement la requête au service de cours
            response = requests.put(
                url,
                data=request.body,
                headers=headers,
                timeout=30
            )
            
            print(f"📡 Réponse: {response.status_code}")
            print(f"📦 Contenu: {response.text[:200]}")
            
            if response.status_code in [200, 201]:
                return JsonResponse(response.json())
            else:
                return JsonResponse(
                    {'error': f'Erreur {response.status_code}: {response.text[:100]}'},
                    status=response.status_code
                )
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
def try_local_token_fallback(request, token):
    """Fallback pour vérifier le token localement si auth_server est down"""
    print("🔄 Tentative de vérification locale du token")
    
    try:
        # Pour l'instant, on accepte simplement le token sans vérification
        # Dans une vraie application, vous décoderiez le JWT ici
        print(f"⚠️ Mode fallback activé pour token: {token[:30]}...")
        
        # Créer des données utilisateur minimales
        user_data = {
            'username': 'user_fallback',
            'user_type': 'student',
            'id': 0
        }
        
        # Stocker dans la session
        request.session['auth_token'] = token
        request.session['user_data'] = user_data
        request.session.modified = True
        
        messages.warning(request, 'Connexion en mode fallback (serveur auth indisponible)')
        
        # Rediriger vers le dashboard utilisateur
        return redirect('utilisateur_dashboard')
            
    except Exception as e:
        print(f"❌ Fallback échoué: {e}")
        messages.error(request, 'Échec de l\'authentification')
        return redirect('home')

# pages/views.py - MODIFIEZ cette fonction
def serve_course_image(request, image_path):
    """
    Rediriger vers le serveur de cours pour les images.
    Les images sont stockées sur le serveur de cours (8002).
    """
    print(f"🖼️ Redirection image vers serveur de cours: {image_path}")
    
    # Rediriger vers le serveur de cours
    from django.shortcuts import redirect
    return redirect(f'http://127.0.0.1:8002/media/course_covers/{image_path}')
def serve_default_image():
    """Servir une image par défaut"""
    try:
        default_image_path = os.path.join(settings.STATIC_ROOT, 'images/default-course.jpg')
        if not os.path.exists(default_image_path):
            default_image_path = os.path.join(settings.BASE_DIR, 'pages/static/images/default-course.jpg')
        
        if os.path.exists(default_image_path):
            with open(default_image_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/jpeg')
    except:
        pass
    
    # Retourner une réponse 404 simple
    from django.http import HttpResponseNotFound
    return HttpResponseNotFound("Default image not found")
@csrf_exempt
def proxy_course_image(request, image_path):
    """
    Proxy pour les images du serveur de cours.
    Permet d'afficher les images depuis le main server même si elles sont stockées sur le serveur de cours.
    """
    try:
        print(f"🖼️ Proxy image: {image_path}")
        
        # URL de l'image sur le serveur de cours
        image_url = f"http://127.0.0.1:8002/media/course_covers/{image_path}"
        
        print(f"🌐 Récupération depuis: {image_url}")
        
        # Récupérer l'image depuis le serveur de cours
        response = requests.get(image_url, stream=True, timeout=10)
        
        print(f"📡 Réponse serveur cours: {response.status_code}")
        
        if response.status_code == 200:
            # Retourner l'image avec le bon content-type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            return HttpResponse(
                response.content,
                content_type=content_type,
                status=200
            )
        else:
            # Retourner une image par défaut
            return serve_default_image()
                
    except Exception as e:
        print(f"💥 Erreur proxy image: {e}")
        return serve_default_image()

def serve_default_image():
    """Servir une image par défaut"""
    try:
        default_image_path = os.path.join(settings.STATIC_ROOT, 'images/default-course.jpg')
        if not os.path.exists(default_image_path):
            default_image_path = os.path.join(settings.BASE_DIR, 'pages/static/images/default-course.jpg')
        
        if os.path.exists(default_image_path):
            with open(default_image_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/jpeg')
    except:
        pass
    
    # Retourner une réponse 404 simple
    from django.http import HttpResponseNotFound
    return HttpResponseNotFound("Image not found")




# main_server/pages/views.py - AJOUTEZ ces fonctions

@csrf_exempt
@require_http_methods(["PUT"])
def api_update_profile(request):
    """Proxy pour mettre à jour le profil utilisateur"""
    print("=" * 60)
    print("🔄 [api_update_profile] DÉBUT")
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    print(f"🔑 Token reçu: {token[:30]}..." if token else "❌ Pas de token")
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = AuthService.verify_token(token)
        print(f"✅ Token valide: {is_valid}, User: {user_data.get('username') if user_data else 'N/A'}")
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Invalid token'
            }, status=401)
        
        # Lire le corps de la requête
        body_bytes = request.body
        print(f"📦 Body bytes reçu: {len(body_bytes)} bytes")
        
        if not body_bytes:
            print("❌ Body vide")
            return JsonResponse({
                'success': False,
                'error': 'Données manquantes'
            }, status=400)
        
        # Essayer de parser le JSON
        try:
            body_str = body_bytes.decode('utf-8')
            print(f"📋 Body string: {body_str[:200]}...")
            
            profile_data = json.loads(body_str)
            print(f"✅ JSON parsé: {profile_data}")
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Format JSON invalide: {str(e)}'
            }, status=400)
        
        # DEBUG: Afficher les données reçues
        print(f"📝 Données à envoyer à auth server:")
        for key, value in profile_data.items():
            print(f"   {key}: {value}")
        
        # CORRECTION ICI : Ajouter /api/auth/ dans l'URL
        auth_service_url = settings.AUTH_SERVICE_URL.rstrip('/')
        url = f"{auth_service_url}/api/auth/profile/update/"  # ← AJOUTEZ /api/auth/
        
        print(f"🌐 Envoi à auth server: {url}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.put(
            url,
            json=profile_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Réponse auth server: {response.status_code}")
        print(f"📦 Contenu réponse: {response.text[:500]}...")
        
        # Gérer la réponse (mieux gérer les réponses vides)
        if response.status_code == 200:
            try:
                if response.text and response.text.strip():
                    response_data = response.json()
                    print(f"✅ Réponse JSON valide")
                    return JsonResponse(response_data, status=200)
                else:
                    print("⚠️ Réponse 200 mais vide, considérer comme succès")
                    return JsonResponse({
                        'success': True,
                        'message': 'Profil mis à jour avec succès'
                    })
            except json.JSONDecodeError:
                print(f"⚠️ Réponse non-JSON mais status 200: {response.text[:100]}")
                return JsonResponse({
                    'success': True,
                    'message': 'Profil mis à jour',
                    'raw_response': response.text[:100] if response.text else ''
                })
        else:
            # Pour les autres status codes
            try:
                if response.text and response.text.strip():
                    error_data = response.json()
                    return JsonResponse({
                        'success': False,
                        'error': error_data.get('error', f'Erreur {response.status_code}')
                    }, status=response.status_code)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'Erreur {response.status_code}: Réponse vide'
                    }, status=response.status_code)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur {response.status_code}',
                    'details': response.text[:200] if response.text else 'Pas de détails'
                }, status=response.status_code)
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Auth server indisponible")
        return JsonResponse({
            'success': False,
            'error': 'Serveur d\'authentification indisponible'
        }, status=503)
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur interne: {str(e)}'
        }, status=500)
    
    finally:
        print("🔄 [api_update_profile] FIN")
        print("=" * 60)
@csrf_exempt
@require_http_methods(["POST"])
def api_update_password(request):
    """Proxy pour changer le mot de passe"""
    print("=" * 60)
    print("🔄 [api_update_password] DÉBUT")
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    print(f"🔑 Token reçu: {token[:30]}..." if token else "❌ Pas de token")
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = AuthService.verify_token(token)
        print(f"✅ Token valide: {is_valid}, User: {user_data.get('username') if user_data else 'N/A'}")
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Invalid token'
            }, status=401)
        
        # Lire les données
        try:
            body_bytes = request.body
            if not body_bytes:
                return JsonResponse({
                    'success': False,
                    'error': 'Données manquantes'
                }, status=400)
            
            password_data = json.loads(body_bytes.decode('utf-8'))
            print(f"📝 Données reçues: {list(password_data.keys())}")
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Format JSON invalide: {str(e)}'
            }, status=400)
        
        # CORRECTION ICI : Ajouter /api/auth/ dans l'URL
        auth_service_url = settings.AUTH_SERVICE_URL.rstrip('/')
        url = f"{auth_service_url}/api/auth/profile/password/"  # ← AJOUTEZ /api/auth/
        
        print(f"🌐 Envoi à auth server: {url}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            url,
            json=password_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Réponse auth server: {response.status_code}")
        print(f"📦 Contenu réponse: {response.text[:200]}...")
        
        # Si le changement de mot de passe réussit, mettre à jour le token
        if response.status_code == 200:
            try:
                if response.text and response.text.strip():
                    data = response.json()
                    print(f"✅ Réponse JSON: {data.get('success', 'N/A')}")
                    
                    if data.get('success'):
                        # Mettre à jour le token dans la session
                        if 'tokens' in data:
                            request.session['auth_token'] = data['tokens']['access_token']
                            request.session.modified = True
                            print(f"🔑 Token mis à jour dans la session")
                        
                        return JsonResponse(data, status=200)
                    else:
                        return JsonResponse(data, status=400)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Réponse vide du serveur d\'authentification'
                    }, status=500)
                    
            except json.JSONDecodeError:
                print(f"❌ Réponse JSON invalide: {response.text}")
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur: Réponse invalide du serveur d\'authentification'
                }, status=500)
        else:
            # Gérer les autres codes de statut
            try:
                if response.text and response.text.strip():
                    error_data = response.json()
                    return JsonResponse({
                        'success': False,
                        'error': error_data.get('error', f'Erreur {response.status_code}')
                    }, status=response.status_code)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'Erreur {response.status_code}'
                    }, status=response.status_code)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur {response.status_code}: {response.text[:100]}'
                }, status=response.status_code)
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Auth server indisponible")
        return JsonResponse({
            'success': False,
            'error': 'Serveur d\'authentification indisponible'
        }, status=503)
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur interne: {str(e)}'
        }, status=500)
    
    finally:
        print("🔄 [api_update_password] FIN")
        print("=" * 60)

# main_server/pages/views.py - MODIFIEZ api_upload_profile_photo

@csrf_exempt
@require_http_methods(["POST"])
def api_upload_profile_photo(request):
    """Proxy pour uploader une photo de profil - VERSION CORRIGÉE"""
    print("=" * 60)
    print("🔄 [api_upload_profile_photo - MAIN SERVER] DÉBUT")
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    print(f"🔑 Token reçu: {token[:30]}..." if token else "❌ Pas de token")
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = AuthService.verify_token(token)
        print(f"✅ Token valide: {is_valid}, User: {user_data.get('username') if user_data else 'N/A'}")
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Invalid token'
            }, status=401)
        
        # Vérifier s'il y a un fichier
        if 'photo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Aucune photo fournie'
            }, status=400)
        
        photo = request.FILES['photo']
        print(f"Fichier reçu: {photo.name} ({photo.size} bytes, {photo.content_type})")
        
        # Validation du fichier
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if photo.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': f'Type de fichier non autorisé. Types acceptés: {", ".join(allowed_types)}'
            }, status=400)
        
        # Vérifier la taille (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if photo.size > max_size:
            return JsonResponse({
                'success': False,
                'error': f'La photo est trop grande. Taille max: {max_size//1024//1024}MB'
            }, status=400)
        
        # URL de l'auth server - CORRECTION ICI
        auth_service_url = settings.AUTH_SERVICE_URL.rstrip('/')
        url = f"{auth_service_url}/api/auth/profile/photo/"
        
        print(f"🌐 Envoi à auth server: {url}")
        
        # Préparer les données pour l'envoi
        files = {'photo': (photo.name, photo, photo.content_type)}
        
        # Envoyer à l'auth server
        response = requests.post(
            url,
            files=files,
            headers={'Authorization': f'Bearer {token}'},
            timeout=30
        )
        
        print(f"📡 Réponse auth server: {response.status_code}")
        
        # Gérer la réponse
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Réponse JSON: {data}")
                
                if data.get('success'):
                    # IMPORTANT: Construire l'URL pour le proxy du main server
                    # L'auth server retourne: /media/profiles/filename.jpg
                    # Le main server proxy utilise: /media/profile_photos/filename.jpg
                    
                    photo_url = data.get('photo_url', '')
                    if photo_url:
                        # Extraire le nom de fichier
                        filename = photo_url.split('/')[-1]
                        
                        # Construire l'URL pour le proxy du main server
                        proxy_url = f"/media/profile_photos/{filename}"
                        
                        print(f"URL original (auth server): {photo_url}")
                        print(f"URL proxy (main server): {proxy_url}")
                        
                        # Mettre à jour le user_data dans la session
                        if 'user_data' in request.session:
                            request.session['user_data']['photo_profil'] = photo_url
                            request.session.modified = True
                            print(f"💾 Session mise à jour avec nouvelle photo")
                        
                        # Retourner l'URL du proxy
                        data['photo_url'] = proxy_url
                        data['original_url'] = photo_url
                    
                    return JsonResponse(data, status=200)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': data.get('error', 'Erreur inconnue')
                    }, status=400)
                    
            except json.JSONDecodeError as e:
                print(f"❌ Erreur parsing JSON: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'Format de réponse invalide: {str(e)}'
                }, status=500)
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text[:200]}")
            return JsonResponse({
                'success': False,
                'error': f'Erreur {response.status_code} du serveur d\'authentification'
            }, status=response.status_code)
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Serveur d\'authentification indisponible'
        }, status=503)
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur interne: {str(e)}'
        }, status=500)
    
    finally:
        print("🔄 [api_upload_profile_photo - MAIN SERVER] FIN")
        print("=" * 60)
# main_server/pages/views.py - AJOUTEZ CETTE FONCTION
@csrf_exempt
def serve_course_pdf(request, pdf_name):
    """Serve le PDF d'un cours - REDIRIGE vers le serveur de cours"""
    try:
        print(f"📄 Demande PDF: {pdf_name}")
        
        # Nettoyer le nom du fichier
        pdf_name = unquote(pdf_name)
        
        # URL du PDF sur le serveur de cours
        pdf_url = f"{settings.COURSES_SERVICE_URL}/media/course_documents/{pdf_name}"
        
        print(f"🌐 Redirection vers: {pdf_url}")
        
        # Récupérer le PDF depuis le serveur de cours
        response = requests.get(pdf_url, stream=True, timeout=30)
        
        print(f"📡 Réponse serveur cours: {response.status_code}")
        
        if response.status_code == 200:
            # Retourner le PDF avec les bons headers
            pdf_response = HttpResponse(
                response.content,
                content_type='application/pdf',
                status=200
            )
            pdf_response['Content-Disposition'] = f'inline; filename="{pdf_name}"'
            pdf_response['X-Frame-Options'] = 'ALLOWALL'  # Permet l'affichage en iframe
            
            print(f"✅ PDF servi avec succès: {pdf_name}")
            return pdf_response
            
        else:
            print(f"❌ PDF non trouvé sur serveur cours: {response.status_code}")
            
            # Retourner une page d'erreur
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>PDF non trouvé</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background: #f8f9fa;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 30px;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #dc3545;
                    }}
                    .error-details {{
                        margin-top: 20px;
                        padding: 15px;
                        background: #f8d7da;
                        border-radius: 5px;
                        text-align: left;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📄 PDF non disponible</h1>
                    <p>Le fichier <strong>{pdf_name}</strong> n'a pas été trouvé.</p>
                    
                    <div class="error-details">
                        <p><strong>URL recherchée:</strong></p>
                        <p><code>{pdf_url}</code></p>
                        <p><strong>Statut HTTP:</strong> {response.status_code}</p>
                    </div>
                    
                    <div style="margin-top: 30px;">
                        <button onclick="window.close()" style="
                            padding: 10px 20px;
                            background: #6c757d;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                        ">
                            Fermer
                        </button>
                    </div>
                </div>
            </body>
            </html>
            """
            return HttpResponse(error_html, status=404, content_type='text/html')
            
    except Exception as e:
        print(f"💥 Erreur serve_course_pdf: {e}")
        import traceback
        traceback.print_exc()
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Erreur serveur</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #dc3545;">❌ Erreur serveur</h1>
            <p>Une erreur est survenue lors du chargement du PDF.</p>
            <div style="margin-top: 20px; padding: 15px; background: #f8d7da; border-radius: 5px; display: inline-block;">
                <p><strong>Détails:</strong></p>
                <p>{str(e)}</p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(error_html, status=500, content_type='text/html')
@csrf_exempt
def proxy_profile_image(request, image_path):
    try:
        # Décoder le chemin
        image_path = unquote(image_path)
        print(f"🖼️ Proxy photo profil: {image_path}")
        
        # Nettoyer le chemin - ENLEVEZ 'profile_photos/' si présent
        if image_path.startswith('profile_photos/'):
            image_path = image_path.replace('profile_photos/', '', 1)
        
        # URL CORRECTE pour l'auth server
        # Les photos sont dans /media/profiles/ sur l'auth server
        image_url = f"http://127.0.0.1:8001/media/profiles/{image_path}"
        
        print(f"🌐 Récupération depuis auth server: {image_url}")
        
        # Récupérer l'image depuis l'auth server
        response = requests.get(image_url, stream=True, timeout=10)
        
        print(f"📡 Réponse auth server: {response.status_code}")
        
        if response.status_code == 200:
            # Déterminer le content-type
            content_type = response.headers.get('Content-Type')
            if not content_type:
                # Deviner à partir de l'extension
                ext = os.path.splitext(image_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    content_type = 'image/jpeg'
                elif ext == '.png':
                    content_type = 'image/png'
                elif ext == '.gif':
                    content_type = 'image/gif'
                else:
                    content_type = 'image/jpeg'  # Par défaut
            
            # Ajouter des headers pour éviter le cache
            headers = {
                'Content-Type': content_type,
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
            }
            
            return HttpResponse(
                response.content,
                content_type=content_type,
                status=200,
                headers=headers
            )
        else:
            print(f"⚠️ Erreur {response.status_code} pour {image_url}")
            print(f"⚠️ Contenu réponse: {response.text[:200]}")
            return serve_default_profile_image()
                
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return serve_default_profile_image()
    except Exception as e:
        print(f"💥 Erreur proxy photo profil: {e}")
        import traceback
        traceback.print_exc()
        return serve_default_profile_image()

def serve_default_profile_image():
    """Servir une image de profil par défaut"""
    try:
        default_image_path = os.path.join(settings.BASE_DIR, 'pages/static/images/default-avatar.png')
        if not os.path.exists(default_image_path):
           default_image_path = os.path.join(settings.BASE_DIR, 'pages/static/images/default-avatar.png')
        
        if os.path.exists(default_image_path):
            with open(default_image_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
    except:
        pass
    
    # Retourner une réponse 404 simple
    from django.http import HttpResponseNotFound
    return HttpResponseNotFound("Default profile image not found")

# views.py - Ajoutez cette fonction
@csrf_exempt
@require_http_methods(["POST"])
def api_enroll_course(request, course_id):
    """API endpoint pour s'inscrire/sauvegarder un cours - Version sans modèle"""
    print(f"🎓 Demande d'inscription au cours ID: {course_id}")
    
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.session.get('auth_token')
    
    if not token:
        print("❌ Pas de token")
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = AuthService.verify_token(token)
        if not is_valid:
            print("❌ Token invalide")
            return JsonResponse({
                'success': False,
                'error': 'Invalid token'
            }, status=401)
        
        user_id = user_data.get('id')
        username = user_data.get('username', 'Utilisateur')
        
        if not user_id:
            print("❌ Pas d'ID utilisateur")
            return JsonResponse({
                'success': False,
                'error': 'User ID not found'
            }, status=400)
        
        print(f"✅ Utilisateur {username} (ID: {user_id}) veut s'inscrire au cours {course_id}")
        
        # Vérifier si le cours existe dans le serveur de cours
        courses_service_url = settings.COURSES_SERVICE_URL.rstrip('/')
        course_response = requests.get(
            f"{courses_service_url}/api/courses/{course_id}/",
            headers={'Authorization': f'Bearer {token}'},
            timeout=5
        )
        
        if course_response.status_code != 200:
            print(f"❌ Cours {course_id} non trouvé sur serveur de cours")
            return JsonResponse({
                'success': False,
                'error': 'Cours non trouvé'
            }, status=404)
        
        course_data = course_response.json()
        print(f"✅ Cours trouvé: {course_data.get('title')}")
        
        # ========== GESTION DES INSCRIPTIONS DANS LA SESSION ==========
        
        # Initialiser la liste des inscriptions si elle n'existe pas
        if 'enrollments' not in request.session:
            request.session['enrollments'] = []
        
        # Vérifier si l'utilisateur est déjà inscrit à ce cours
        enrollments = request.session['enrollments']
        
        # Trouver les inscriptions de cet utilisateur
        user_enrollments = [
            e for e in enrollments 
            if e.get('user_id') == user_id and e.get('course_id') == course_id
        ]
        
        if user_enrollments:
            print(f"⚠️ Utilisateur déjà inscrit à ce cours")
            return JsonResponse({
                'success': False,
                'error': 'Vous êtes déjà inscrit à ce cours'
            }, status=400)
        
        # Créer une nouvelle inscription
        enrollment_data = {
            'user_id': user_id,
            'username': username,
            'course_id': course_id,
            'course_title': course_data.get('title', 'Cours sans titre'),
            'course_type': course_data.get('course_type', 'free'),
            'enrollment_date': timezone.now().isoformat(),
            'progress': 0,
            'status': 'not_started',
            'last_accessed': timezone.now().isoformat(),
            'media_type': course_data.get('media_type', 'pdf'),
            'pages': course_data.get('pages', 0),
            'duration_hours': course_data.get('duration_hours', 0),
            'cover_photo': course_data.get('cover_photo', ''),
            'instructor_name': course_data.get('instructor_name', 'Admin')
        }
        
        # Ajouter à la session
        enrollments.append(enrollment_data)
        request.session['enrollments'] = enrollments
        request.session.modified = True
        
        print(f"✅ Inscription sauvegardée dans la session")
        print(f"📊 Total d'inscriptions: {len(enrollments)}")
        
        # Récupérer également les détails du cours pour les stocker séparément
        if 'my_courses' not in request.session:
            request.session['my_courses'] = {}
        
        # Stocker les informations du cours
        request.session['my_courses'][str(course_id)] = {
            'title': course_data.get('title'),
            'description': course_data.get('description'),
            'short_description': course_data.get('short_description'),
            'media_type': course_data.get('media_type', 'pdf'),
            'pages': course_data.get('pages', 0),
            'duration_hours': course_data.get('duration_hours', 0),
            'cover_photo': course_data.get('cover_photo', ''),
            'instructor_name': course_data.get('instructor_name', 'Admin'),
            'enrolled_at': timezone.now().isoformat()
        }
        
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': 'Cours ajouté à votre liste avec succès',
            'enrollment': enrollment_data,
            'course': course_data
        })
        
    except requests.exceptions.ConnectionError:
        print("❌ Serveur de cours indisponible")
        return JsonResponse({
            'success': False,
            'error': 'Serveur de cours indisponible'
        }, status=503)
    except Exception as e:
        print(f"💥 Erreur lors de l'inscription: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



@csrf_exempt
@require_http_methods(["GET"])
def api_get_my_courses(request):
    """API pour récupérer les cours de l'utilisateur"""
    token = get_token_from_request(request)
    
    if not token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    is_valid, user_data = AuthService.verify_token(token)
    if not is_valid:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    
    user_id = user_data.get('id')
    
    # Récupérer les inscriptions depuis la session
    enrollments = request.session.get('enrollments', [])
    user_enrollments = [
        e for e in enrollments 
        if e.get('user_id') == user_id
    ]
    
    print(f"📚 Cours de l'utilisateur {user_id}: {len(user_enrollments)} inscriptions")
    
    # Pour chaque inscription, récupérer les détails du cours
    courses_with_details = []
    
    for enrollment in user_enrollments:
        course_id = enrollment.get('course_id')
        
        try:
            # Récupérer les détails du cours
            course_info = get_course_info(course_id, token)
            
            if course_info:
                course_with_enrollment = {
                    **course_info,
                    'enrollment': enrollment,
                    'is_enrolled': True,
                    'user_progress': enrollment.get('progress', 0),
                    'user_status': enrollment.get('status', 'not_started')
                }
                courses_with_details.append(course_with_enrollment)
                
        except Exception as e:
            print(f"⚠️ Erreur récupération cours {course_id}: {e}")
            # Ajouter quand même avec les infos de base
            courses_with_details.append({
                'id': course_id,
                'title': enrollment.get('course_title', f'Cours #{course_id}'),
                'enrollment': enrollment,
                'is_enrolled': True
            })
    
    return JsonResponse({
        'success': True,
        'count': len(courses_with_details),
        'courses': courses_with_details
    })
