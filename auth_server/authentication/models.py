from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import secrets
from datetime import timedelta

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrateur'),
        ('etudiant', 'Étudiant'),
    )
    
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPE_CHOICES,
        default='etudiant'
    )
    
    # Champs supplémentaires
    date_naissance = models.DateField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    
    # Champs pour l'API distribué
    api_token = models.CharField(max_length=255, blank=True, null=True, unique=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    refresh_token = models.CharField(max_length=255, blank=True, null=True, unique=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def generate_api_token(self):
        """Génère un token API valide 7 jours"""
        from datetime import datetime
        self.api_token = secrets.token_urlsafe(64)
        self.token_expiry = datetime.now() + timedelta(days=7)
        self.refresh_token = secrets.token_urlsafe(64)
        self.save()
        return {
            'access_token': self.api_token,
            'refresh_token': self.refresh_token,
            'expires_in': 604800  # 7 jours en secondes
        }
    
    def refresh_api_token(self):
        """Rafraîchit le token avec le refresh token"""
        from datetime import datetime
        if self.refresh_token:
            self.api_token = secrets.token_urlsafe(64)
            self.token_expiry = datetime.now() + timedelta(days=7)
            self.save()
            return self.api_token
        return None
    
    def is_token_valid(self):
        """Vérifie si le token est valide"""
        if not self.api_token or not self.token_expiry:
            return False
        return self.token_expiry > timezone.now()
        