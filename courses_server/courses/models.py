from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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