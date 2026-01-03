from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import secrets
from datetime import timedelta
import os

def user_profile_upload_path(instance, filename):
    """Génère le chemin de sauvegarde pour les photos de profil"""
    # Format: profiles/user_id/filename
    ext = filename.split('.')[-1]
    filename = f"profile_{instance.id}.{ext}"
    return os.path.join('profiles', str(instance.id), filename)

class User(AbstractUser):
    # Supprimez le champ user_type des choix - il sera géré automatiquement
    # USER_TYPE_CHOICES = (
    #     ('admin', 'Administrateur'),
    #     ('etudiant', 'Étudiant'),
    # )
    
    # Champ user_type gardé pour compatibilité, mais géré automatiquement
    user_type = models.CharField(
        max_length=20,
        default='etudiant',
        verbose_name='Type d\'utilisateur'
    )
    
    # Champs existants
    date_naissance = models.DateField(
        blank=True, 
        null=True,
        verbose_name='Date de naissance'
    )
    
    telephone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Téléphone'
    )
    
    # NOUVEAUX CHAMPS AJOUTÉS
    photo_profil = models.ImageField(
        upload_to=user_profile_upload_path,
        blank=True,
        null=True,
        verbose_name='Photo de profil',
        help_text='Téléchargez une photo de profil (format recommandé: carré, max 2MB)'
    )
    
    PAYS_CHOICES = [
        ('MA', 'Maroc'),
        ('FR', 'France'),
        ('BE', 'Belgique'),
        ('CA', 'Canada'),
        ('TN', 'Tunisie'),
        ('DZ', 'Algérie'),
        ('SN', 'Sénégal'),
        ('CI', 'Côte d\'Ivoire'),
        ('OTHER', 'Autre pays'),
    ]
    
    pays = models.CharField(
        max_length=50,
        choices=PAYS_CHOICES,
        default='MA',
        blank=True,
        verbose_name='Pays',
        help_text='Sélectionnez votre pays de résidence'
    )
    
    LANGUE_CHOICES = [
        ('fr', 'Français'),
        ('ar', 'Arabe'),
        ('en', 'Anglais'),
        ('es', 'Espagnol'),
        ('de', 'Allemand'),
        ('OTHER', 'Autre langue'),
    ]
    
    langue = models.CharField(
        max_length=20,
        choices=LANGUE_CHOICES,
        default='fr',
        blank=True,
        verbose_name='Langue préférée',
        help_text='Sélectionnez votre langue préférée'
    )
    
    # Champs pour l'API distribué
    api_token = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        unique=True,
        verbose_name='Token API'
    )
    
    token_expiry = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='Expiration du token'
    )
    
    refresh_token = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        unique=True,
        verbose_name='Refresh Token'
    )
    
    # Champs de métadonnées supplémentaires
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Biographie',
        help_text='Présentez-vous en quelques mots'
    )
    
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name='Site web personnel'
    )
    
    linkedin = models.URLField(
        blank=True,
        null=True,
        verbose_name='Profil LinkedIn'
    )
    
    github = models.URLField(
        blank=True,
        null=True,
        verbose_name='Profil GitHub'
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name='Dernière modification'
    )
    
    # Gestion des permissions basée sur is_superuser
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['pays']),
            models.Index(fields=['langue']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        if self.is_superuser:
            return f"{self.username} (Administrateur)"
        return f"{self.username} (Étudiant)"
    
    def save(self, *args, **kwargs):
        """S'assurer que user_type correspond à is_superuser"""
        # Si c'est un superuser, forcer user_type='admin'
        if self.is_superuser:
            self.user_type = 'admin'
            self.is_staff = True  # Les admins ont accès à l'interface admin
        else:
            # Pour les inscriptions via formulaire, toujours étudiant
            self.user_type = 'etudiant'
            self.is_staff = False
        
        # S'assurer que l'email est unique
        if self.email:
            self.email = self.email.lower()
        
        super().save(*args, **kwargs)
    
    def get_user_type_display(self):
        """Retourne le type d'utilisateur formaté"""
        if self.is_superuser:
            return "Administrateur"
        return "Étudiant"
    
    def is_admin_user(self):
        """Vérifie si l'utilisateur est admin (basé sur is_superuser)"""
        return self.is_superuser
    
    def generate_api_token(self):
        """Génère un token API valide 7 jours"""
        # Utiliser timezone.now() au lieu de datetime.now() pour supporter les timezones
        self.api_token = secrets.token_urlsafe(64)
        self.token_expiry = timezone.now() + timedelta(days=7)
        self.refresh_token = secrets.token_urlsafe(64)
        self.save()
        return {
            'access_token': self.api_token,
            'refresh_token': self.refresh_token,
            'expires_in': 604800,  # 7 jours en secondes
            'expires_at': self.token_expiry.isoformat()
        }
    
    def refresh_api_token(self):
        """Rafraîchit le token avec le refresh token"""
        if self.refresh_token and self.token_expiry > timezone.now():
            self.api_token = secrets.token_urlsafe(64)
            self.token_expiry = timezone.now() + timedelta(days=7)
            self.save()
            return self.api_token
        return None
    
    def is_token_valid(self):
        """Vérifie si le token est valide"""
        if not self.api_token or not self.token_expiry:
            return False
        return self.token_expiry > timezone.now()
    
    def get_profile_picture_url(self):
        """Retourne l'URL de la photo de profil ou une image par défaut"""
        if self.photo_profil and hasattr(self.photo_profil, 'url'):
            return self.photo_profil.url
        # Retourner une image par défaut
        return '/static/images/default-profile.png'
    
    def get_age(self):
        """Calcule l'âge de l'utilisateur si date_naissance existe"""
        if self.date_naissance:
            today = timezone.now().date()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        name_parts = []
        if self.first_name:
            name_parts.append(self.first_name)
        if self.last_name:
            name_parts.append(self.last_name)
        return ' '.join(name_parts) if name_parts else self.username
    
    def clean(self):
        """Validation supplémentaire avant sauvegarde"""
        from django.core.exceptions import ValidationError
        
        # Valider la date de naissance
        if self.date_naissance:
            if self.date_naissance > timezone.now().date():
                raise ValidationError({'date_naissance': 'La date de naissance ne peut pas être dans le futur.'})
            
            # Vérifier l'âge minimum (13 ans)
            age = self.get_age()
            if age and age < 13:
                raise ValidationError({'date_naissance': 'Vous devez avoir au moins 13 ans pour vous inscrire.'})
    
    def delete_profile_picture(self):
        """Supprime la photo de profil du stockage"""
        if self.photo_profil:
            # Supprimer le fichier physique
            storage = self.photo_profil.storage
            if storage.exists(self.photo_profil.name):
                storage.delete(self.photo_profil.name)
            # Supprimer la référence dans la base de données
            self.photo_profil = None
            self.save()