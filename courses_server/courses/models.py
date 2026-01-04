from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import secrets
from datetime import timedelta
class Category(models.Model):
    """Catégorie des cours (ex: Développement Web, Data Science, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Course(models.Model):
    """Modèle principal pour les cours - MODIFIÉ pour inclure documents/vidéos directement"""
    COURSE_TYPES = [
        ('free', 'Gratuit'),
        ('paid', 'Payant'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]
    
    # ✅ NOUVEAU : Type de média
    MEDIA_TYPE_CHOICES = [
        ('pdf', 'Document PDF'),
        ('video', 'Vidéo'),
        ('mixed', 'Mixte (PDF + Vidéo)'),
    ]
    
    # Informations de base
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    
    # ✅ NOUVEAU : Type de média
    media_type = models.CharField(
        max_length=10, 
        choices=MEDIA_TYPE_CHOICES, 
        default='pdf',
        help_text="Type principal du contenu"
    )
    
    # Catégorie et classification
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    course_type = models.CharField(max_length=10, choices=COURSE_TYPES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    
    # Informations pédagogiques
    objectives = models.TextField(blank=True, help_text="Objectifs d'apprentissage")
    prerequisites = models.TextField(blank=True, help_text="Prérequis")
    target_audience = models.TextField(blank=True, help_text="Public cible")
    
    # Métadonnées
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # ✅ MODIFIÉ : Durée et pages
    duration_hours = models.PositiveIntegerField(
        default=0, 
        help_text="Durée totale en heures (pour vidéos)"
    )
    pages = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de pages (pour PDFs)"
    )
    
    # Images
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    cover_photo = models.ImageField(
        upload_to='course_covers/',
        blank=True,
        null=True,
        help_text="Photo de couverture du cours"
    )
    
    # ✅ CHAMPS POUR CONTENU DIRECT
    # Pour les vidéos
    preview_video_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL de la vidéo (YouTube, Vimeo, etc.)"
    )
    
    # ✅ NOUVEAU : Pour les documents PDF
    document_file = models.FileField(
        upload_to='course_documents/',
        blank=True,
        null=True,
        help_text="Document PDF du cours"
    )
    
    # Statistiques
    total_students = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Relations avec d'autres systèmes
    instructor_id = models.IntegerField()  # ID de l'instructeur (depuis auth_server)
    instructor_name = models.CharField(max_length=200, blank=True)
    
    # Métadonnées techniques
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    language = models.CharField(max_length=50, default='Français')
    tags = models.CharField(max_length=500, blank=True, help_text="Tags séparés par des virgules")
    
    # Configuration
    is_featured = models.BooleanField(default=False)
    certificate_available = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'course_type']),
            models.Index(fields=['instructor_id']),
            models.Index(fields=['media_type']),  # ✅ Nouvel index
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_discounted(self):
        return self.discount_price is not None and self.discount_price < self.price
    
    # ✅ NOUVEAU : Propriétés pour faciliter l'identification
    @property
    def is_pdf_course(self):
        return self.media_type == 'pdf' or (self.document_file and not self.preview_video_url)
    
    @property
    def is_video_course(self):
        return self.media_type == 'video' or (self.preview_video_url and not self.document_file)
    
    @property
    def is_mixed_course(self):
        return self.media_type == 'mixed' or (self.document_file and self.preview_video_url)


    def enroll_student(self, user_id, user_data=None):
        """Inscrire un étudiant à ce cours"""
        from .models import Enrollment
        
        # Vérifier si déjà inscrit
        existing = Enrollment.objects.filter(
            user_id=user_id,
            course=self,
            is_active=True
        ).first()
        
        if existing:
            return {
                'success': False,
                'error': 'Déjà inscrit à ce cours',
                'enrollment': existing
            }
        
        # Créer l'inscription
        try:
            enrollment = Enrollment.objects.create(
                user_id=user_id,
                course=self,
                user_username=user_data.get('username', '') if user_data else '',
                user_email=user_data.get('email', '') if user_data else '',
                user_full_name=user_data.get('full_name', '') if user_data else '',
                enrollment_type='free' if self.course_type == 'free' else 'paid',
                status='not_started',
                progress=0
            )
            
            # Mettre à jour le compteur d'étudiants
            self.total_students += 1
            self.save()
            
            return {
                'success': True,
                'message': 'Inscription réussie',
                'enrollment': enrollment,
                'access_code': enrollment.access_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_enrolled_students_count(self):
        """Nombre d'étudiants inscrits"""
        return self.enrollments.filter(is_active=True).count()
    
    def is_user_enrolled(self, user_id):
        """Vérifier si un utilisateur est inscrit"""
        return self.enrollments.filter(
            user_id=user_id,
            is_active=True
        ).exists()



# ... votre modèle Course existant ...

class Enrollment(models.Model):
    """Modèle pour gérer les inscriptions aux cours (côté cours_server)"""
    STATUS_CHOICES = [
        ('not_started', 'Non commencé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('dropped', 'Abandonné'),
    ]
    
    # IMPORTANT: Dans un système distribué, on ne peut pas faire de ForeignKey
    # vers le modèle User d'une autre base de données
    user_id = models.IntegerField(
        db_index=True,
        help_text="ID de l'utilisateur depuis le serveur d'authentification"
    )
    
    # On peut stocker des infos utilisateur pour éviter trop d'appels API
    user_username = models.CharField(max_length=150, blank=True)
    user_email = models.EmailField(blank=True)
    user_full_name = models.CharField(max_length=255, blank=True)
    
    # Relation vers le cours (même base de données)
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )
    
    # Informations d'inscription
    enrollment_date = models.DateTimeField(auto_now_add=True)
    enrollment_type = models.CharField(
        max_length=20,
        choices=[('free', 'Gratuit'), ('paid', 'Payant')],
        default='free'
    )
    
    # Progression
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='not_started'
    )
    progress = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text="Progression en pourcentage (0-100)"
    )
    
    # Dates importantes
    last_accessed = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    access_code = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Code d'accès unique pour l'étudiant"
    )
    is_active = models.BooleanField(default=True)
    
    # Pour les cours payants
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Notes personnelles
    notes = models.TextField(blank=True, help_text="Notes personnelles sur le cours")
    
    # Synchronisation avec auth_server (pour système distribué)
    last_synced = models.DateTimeField(auto_now=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[('synced', 'Synchronisé'), ('pending', 'En attente'), ('failed', 'Échoué')],
        default='synced'
    )
    
    class Meta:
        unique_together = ['user_id', 'course']  # Un utilisateur ne peut s'inscrire qu'une fois par cours
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['course', 'user_id']),
            models.Index(fields=['enrollment_date']),
            models.Index(fields=['last_accessed']),
            models.Index(fields=['status', 'progress']),
        ]
        ordering = ['-enrollment_date']
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
    
    def __str__(self):
        return f"Enrollment #{self.id} - User {self.user_id} dans {self.course.title}"
    
    def save(self, *args, **kwargs):
        # Générer un code d'accès unique si vide
        if not self.access_code:
            self.access_code = f"COURS-{self.user_id}-{secrets.token_hex(4).upper()}"
        
        # Mettre à jour le statut en fonction de la progression
        if self.progress == 0:
            self.status = 'not_started'
        elif self.progress == 100:
            self.status = 'completed'
            if not self.completion_date:
                self.completion_date = timezone.now()
        elif 0 < self.progress < 100:
            self.status = 'in_progress'
        
        # Mettre à jour la date d'accès
        if not self.last_accessed:
            self.last_accessed = timezone.now()
        
        super().save(*args, **kwargs)
    
    def update_progress(self, new_progress):
        """Mettre à jour la progression"""
        if 0 <= new_progress <= 100:
            self.progress = new_progress
            self.last_accessed = timezone.now()
            self.save()
            return True
        return False
    
    def complete_course(self):
        """Marquer le cours comme terminé"""
        self.progress = 100
        self.status = 'completed'
        self.completion_date = timezone.now()
        self.save()
    
    @property
    def days_since_enrollment(self):
        """Nombre de jours depuis l'inscription"""
        if self.enrollment_date:
            delta = timezone.now() - self.enrollment_date
            return delta.days
        return 0
    
    @property
    def is_expired(self):
        """Vérifier si l'inscription est expirée (après 1 an)"""
        if self.enrollment_date:
            expiration_date = self.enrollment_date + timezone.timedelta(days=365)
            return timezone.now() > expiration_date
        return False
    
    def get_certificate_data(self):
        """Générer les données pour un certificat"""
        return {
            'enrollment_id': self.id,
            'course_title': self.course.title,
            'student_name': self.user_full_name,
            'enrollment_date': self.enrollment_date.strftime('%d/%m/%Y'),
            'completion_date': self.completion_date.strftime('%d/%m/%Y') if self.completion_date else None,
            'access_code': self.access_code,
            'status': self.status,
            'progress': self.progress
        }