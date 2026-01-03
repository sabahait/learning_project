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