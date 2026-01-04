# courses/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.text import slugify
from django.db import transaction
from .models import Course, Category
from .serializers import CourseSerializer, CategorySerializer

# ==== FONCTIONS SIMPLES ====
@require_GET
def health_check(request):
    """Vérifie l'état du service"""
    return JsonResponse({'status': 'healthy', 'service': 'courses_server'})

@require_GET
def api_status(request):
    """Vérifie le statut de l'API"""
    return JsonResponse({'courses_service': 'running', 'database': 'connected'})

# ==== VIEWSETS ====
class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les cours"""
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]  # À changer en production
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrer par statut
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Recherche
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Filtrer par type de média
        media_type = self.request.query_params.get('media_type', None)
        if media_type:
            queryset = queryset.filter(media_type=media_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def pdf(self, request):
        """Récupère uniquement les cours PDF"""
        queryset = self.get_queryset().filter(media_type='pdf')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def video(self, request):
        """Récupère uniquement les cours vidéo"""
        queryset = self.get_queryset().filter(media_type='video')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les catégories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]  # À changer en production
    
    def list(self, request, *args, **kwargs):
        """Crée des catégories par défaut si la table est vide"""
        if not Category.objects.exists():
            print("📦 Table Category vide, création des catégories par défaut...")
            self.create_default_categories()
        return super().list(request, *args, **kwargs)
    
    def create_default_categories(self):
        """Crée les catégories par défaut"""
        default_categories = [
            (1, 'Développement Web', 'HTML, CSS, JavaScript, React, Vue, Angular'),
            (2, 'Data Science', 'Python, Machine Learning, Intelligence Artificielle, Analyse de données'),
            (3, 'Mobile Development', 'Android, iOS, Flutter, React Native'),
            (4, 'Design UI/UX', 'Design d\'interface, Expérience utilisateur, Figma, Adobe XD'),
            (5, 'Business', 'Management, Entrepreneuriat, Marketing, Finance'),
            (6, 'Marketing Digital', 'SEO, Réseaux sociaux, Email marketing, Content marketing'),
        ]
        
        try:
            with transaction.atomic():
                categories_to_create = []
                for id_num, name, description in default_categories:
                    categories_to_create.append(
                        Category(
                            id=id_num,
                            name=name,
                            slug=slugify(name),
                            description=description
                        )
                    )
                Category.objects.bulk_create(categories_to_create)
                print(f"✅ {len(categories_to_create)} catégories créées avec succès")
        except Exception as e:
            print(f"❌ Erreur création catégories: {e}")

# ==== FONCTIONS API SIMPLES ====
@require_GET
def get_courses(request):
    """API simple pour récupérer tous les cours"""
    try:
        courses = Course.objects.all().select_related('category')
        courses_list = []
        
        for course in courses:
            course_data = {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'short_description': course.short_description,
                'price': float(course.price),
                'media_type': course.media_type,
                'preview_video_url': course.preview_video_url,
                'document_file': course.document_file.url if course.document_file else None,
                'document_url': course.document_file.url if course.document_file else None,
                'pages': course.pages,
                'duration_hours': course.duration_hours,
                'category': {
                    'id': course.category.id if course.category else None,
                    'name': course.category.name if course.category else 'Non catégorisé'
                },
                'instructor_name': course.instructor_name,
                'instructor_id': course.instructor_id,
                'cover_photo': course.cover_photo.url if course.cover_photo else None,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'level': course.level,
                'status': course.status,
                'tags': course.tags,
                'created_at': course.created_at.isoformat() if course.created_at else None,
            }
            courses_list.append(course_data)
        
        return JsonResponse({'courses': courses_list})
    
    except Exception as e:
        print(f"❌ Erreur get_courses: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_categories(request):
    """API simple pour récupérer toutes les catégories"""
    try:
        categories = Category.objects.all()
        categories_list = [{'id': cat.id, 'name': cat.name} for cat in categories]
        return JsonResponse({'categories': categories_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_pdf_courses(request):
    """API pour récupérer uniquement les cours PDF"""
    try:
        pdf_courses = Course.objects.filter(media_type='pdf')
        courses_list = []
        
        for course in pdf_courses:
            course_data = {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'price': float(course.price),
                'document_file': course.document_file.url if course.document_file else None,
                'pages': course.pages,
                'category': {
                    'id': course.category.id if course.category else None,
                    'name': course.category.name if course.category else 'Non catégorisé'
                },
                'instructor_name': course.instructor_name,
                'cover_photo': course.cover_photo.url if course.cover_photo else None,
            }
            courses_list.append(course_data)
        
        return JsonResponse({'pdf_courses': courses_list})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_video_courses(request):
    """API pour récupérer uniquement les cours vidéo"""
    try:
        video_courses = Course.objects.filter(media_type='video')
        courses_list = []
        
        for course in video_courses:
            course_data = {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'price': float(course.price),
                'preview_video_url': course.preview_video_url,
                'duration_hours': course.duration_hours,
                'category': {
                    'id': course.category.id if course.category else None,
                    'name': course.category.name if course.category else 'Non catégorisé'
                },
                'instructor_name': course.instructor_name,
                'cover_photo': course.cover_photo.url if course.cover_photo else None,
            }
            courses_list.append(course_data)
        
        return JsonResponse({'video_courses': courses_list})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# courses/views.py - AJOUTEZ ces imports en haut
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
from .models import Course, Enrollment
import json
from rest_framework.decorators import api_view

# AJOUTEZ cette fonction pour vérifier le token
def verify_auth_token(token):
    """Vérifie un token JWT avec le serveur d'authentification"""
    try:
        AUTH_SERVER_URL = "http://127.0.0.1:8001"  # Changez selon votre configuration
        response = requests.post(
            f"{AUTH_SERVER_URL}/api/auth/verify/",
            json={'token': token},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('valid'):
                return True, data.get('user', {})
    except:
        pass
    return False, None

# AJOUTEZ ces vues API d'inscription

@csrf_exempt
@require_POST
def api_enroll_course(request, course_id):
    """API pour inscrire un utilisateur à un cours"""
    print(f"🎓 Demande d'inscription au cours ID: {course_id}")
    
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.POST.get('token')
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Token manquant'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = verify_auth_token(token)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Token invalide ou expiré'
            }, status=401)
        
        user_id = user_data.get('id')
        username = user_data.get('username', 'Utilisateur')
        
        print(f"✅ Utilisateur {username} (ID: {user_id}) veut s'inscrire au cours {course_id}")
        
        # Récupérer le cours
        course = get_object_or_404(Course, id=course_id, status='published')
        
        # Vérifier si déjà inscrit
        existing = Enrollment.objects.filter(
            user_id=user_id,
            course=course,
            is_active=True
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'error': 'Vous êtes déjà inscrit à ce cours',
                'enrollment_id': existing.id
            }, status=400)
        
        # Créer l'inscription
        enrollment = Enrollment.objects.create(
            user_id=user_id,
            course=course,
            user_username=username,
            user_email=user_data.get('email', ''),
            user_full_name=user_data.get('full_name', username),
            enrollment_type='free' if course.course_type == 'free' else 'paid',
            status='not_started',
            progress=0
        )
        
        # Mettre à jour le compteur d'étudiants
        course.total_students += 1
        course.save()
        
        print(f"✅ Inscription créée avec ID: {enrollment.id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Inscription réussie',
            'enrollment': {
                'id': enrollment.id,
                'course_id': course.id,
                'course_title': course.title,
                'access_code': enrollment.access_code,
                'enrollment_date': enrollment.enrollment_date.isoformat(),
                'status': enrollment.status,
                'progress': enrollment.progress
            }
        }, status=201)
        
    except Exception as e:
        print(f"💥 Erreur lors de l'inscription: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_GET
def api_check_enrollment(request, course_id):
    """API pour vérifier si un utilisateur est inscrit à un cours"""
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.GET.get('token')
    
    if not token:
        return JsonResponse({
            'success': False,
            'is_enrolled': False,
            'error': 'Token manquant'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = verify_auth_token(token)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'is_enrolled': False,
                'error': 'Token invalide'
            }, status=401)
        
        user_id = user_data.get('id')
        
        # Vérifier l'inscription
        is_enrolled = Enrollment.objects.filter(
            user_id=user_id,
            course_id=course_id,
            is_active=True
        ).exists()
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'course_id': course_id,
            'is_enrolled': is_enrolled
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'is_enrolled': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_GET
def api_my_courses(request):
    """API pour récupérer les cours de l'utilisateur"""
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.GET.get('token')
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Token manquant'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = verify_auth_token(token)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Token invalide'
            }, status=401)
        
        user_id = user_data.get('id')
        
        # Récupérer les inscriptions
        enrollments = Enrollment.objects.filter(
            user_id=user_id,
            is_active=True
        ).select_related('course', 'course__category').order_by('-enrollment_date')
        
        courses_data = []
        for enrollment in enrollments:
            course = enrollment.course
            
            # Récupérer le nom du fichier PDF
            pdf_filename = None
            if course.document_file:
                pdf_filename = course.document_file.name.split('/')[-1]
            
            courses_data.append({
                'enrollment_id': enrollment.id,
                'course_id': course.id,
                'title': course.title,
                'description': course.short_description,
                'category': course.category.name if course.category else 'Non catégorisé',
                'level': course.level,
                'duration_hours': course.duration_hours,
                'pages': course.pages,
                'price': float(course.price),
                'course_type': course.course_type,
                'media_type': course.media_type,
                
                # Données d'inscription
                'enrollment_date': enrollment.enrollment_date.isoformat(),
                'status': enrollment.status,
                'progress': enrollment.progress,
                'access_code': enrollment.access_code,
                'last_accessed': enrollment.last_accessed.isoformat() if enrollment.last_accessed else None,
                
                # Fichiers
                'document_file': course.document_file.url if course.document_file else None,
                'document_filename': pdf_filename,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                
                # Métadonnées
                'instructor_name': course.instructor_name,
                'average_rating': course.average_rating,
                'certificate_available': course.certificate_available,
            })
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'count': len(courses_data),
            'courses': courses_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_POST
def api_update_progress(request, enrollment_id):
    """API pour mettre à jour la progression d'un cours"""
    # Récupérer le token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        data = json.loads(request.body) if request.body else {}
        token = data.get('token')
    
    if not token:
        return JsonResponse({
            'success': False,
            'error': 'Token manquant'
        }, status=401)
    
    try:
        # Vérifier le token
        is_valid, user_data = verify_auth_token(token)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': 'Token invalide'
            }, status=401)
        
        user_id = user_data.get('id')
        
        # Récupérer l'inscription
        enrollment = get_object_or_404(
            Enrollment, 
            id=enrollment_id,
            user_id=user_id
        )
        
        # Récupérer la progression
        data = json.loads(request.body) if request.body else {}
        progress = data.get('progress')
        
        if progress is None or not (0 <= progress <= 100):
            return JsonResponse({
                'success': False,
                'error': 'Progression invalide (doit être entre 0 et 100)'
            }, status=400)
        
        # Mettre à jour
        enrollment.update_progress(progress)
        
        return JsonResponse({
            'success': True,
            'message': 'Progression mise à jour',
            'progress': enrollment.progress,
            'status': enrollment.status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)