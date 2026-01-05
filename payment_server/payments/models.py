# payment_server/payments/models.py
from django.db import models
import uuid
import secrets
from django.utils import timezone

class PaymentTransaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('rib', 'RIB'),
        ('card', 'Carte bancaire'),
        ('paypal', 'PayPal'),
        ('free', 'Gratuit'),
    ]
    
    # === CORRECTION : Ajoutez une clé primaire AutoField ===
    id = models.AutoField(primary_key=True, verbose_name='ID')
    
    # UUID comme référence unique (pas comme clé primaire)
    transaction_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='UUID Transaction'
    )
    
    user_id = models.IntegerField(
        verbose_name='ID Utilisateur'
    )
    
    # Informations du cours
    course_id = models.IntegerField(
        verbose_name='ID Cours',
        default=0
    )
    course_name = models.CharField(
        max_length=255, 
        verbose_name='Nom du cours',
        default='Cours'
    )
    
    # Montant et statut
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Montant',
        default=0.00
    )
    
    # ... tous les autres champs restent inchangés ...
    # MAIS assurez-vous que tous les champs obligatoires ont une valeur par défaut
    
    # Informations de paiement
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='rib',
        verbose_name='Méthode de paiement'
    )
    
    # Pour RIB
    rib_number = models.CharField(
        max_length=27, 
        blank=True, 
        null=True,
        verbose_name='Numéro RIB'
    )
    rib_holder_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Titulaire du compte'
    )
    
    # Pour carte bancaire
    card_last_four = models.CharField(
        max_length=4, 
        blank=True, 
        null=True,
        verbose_name='4 derniers chiffres'
    )
    card_expiry_month = models.CharField(
        max_length=2, 
        blank=True, 
        null=True,
        verbose_name='Mois d\'expiration'
    )
    card_expiry_year = models.CharField(
        max_length=4, 
        blank=True, 
        null=True,
        verbose_name='Année d\'expiration'
    )
    card_holder_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Nom sur la carte'
    )
    
    # Codes d'accès
    access_code = models.CharField(
        max_length=50, 
        unique=True,
        blank=True,  # AJOUTEZ blank=True
        verbose_name='Code d\'accès'
    )
    enrollment_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Code d\'inscription'
    )
    
    # Statuts
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='Statut'
    )
    enrollment_status = models.CharField(
        max_length=20,
        choices=[
            ('not_created', 'Inscription non créée'),
            ('created', 'Inscription créée'),
            ('failed', 'Échec inscription'),
        ],
        default='not_created',
        verbose_name='Statut inscription'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création'
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Date de complétion'
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Dernière mise à jour'
    )
    
    # Relations
    parent_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_transactions',
        verbose_name='Transaction parente'
    )
    
    # Logs et suivi
    notes = models.TextField(
        blank=True,
        verbose_name='Notes internes'
    )
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True,
        verbose_name='Adresse IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['course_id', 'status']),
            models.Index(fields=['access_code']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'enrollment_status']),
        ]
        verbose_name = 'Transaction de paiement'
        verbose_name_plural = 'Transactions de paiement'
    
    def __str__(self):
        return f"Transaction {self.transaction_uuid} - {self.course_name} - {self.amount}€"
    
    def save(self, *args, **kwargs):
        # Générer les codes si nécessaire
        if not self.access_code:
            self.access_code = self.generate_access_code()
        
        # Si le paiement est complété, mettre à jour la date
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            
        # Si le montant est 0, c'est un cours gratuit
        if self.amount == 0:
            self.payment_method = 'free'
            self.status = 'completed'
        
        super().save(*args, **kwargs)
    
    def generate_access_code(self):
        """Génère un code d'accès unique"""
        import string
        import random
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(characters) for _ in range(12))
        return f"PAY-{code[:4]}-{code[4:8]}-{code[8:12]}"
    
   # payment_server/payments/models.py - AJOUTEZ cette méthode
def create_enrollment_on_course_server(self):
    """Crée l'inscription sur le serveur de cours"""
    try:
        import requests
        
        # Préparer les données pour le serveur de cours
        enrollment_data = {
            'transaction_id': str(self.transaction_uuid),
            'user_id': self.user_id,
            'course_id': self.course_id,
            'access_code': self.access_code,
            'payment_method': self.payment_method,
            'amount': float(self.amount),
            'payment_date': self.completed_at.isoformat() if self.completed_at else timezone.now().isoformat(),
        }
        
        # Appeler l'API du serveur de cours
        response = requests.post(
            'http://127.0.0.1:8002/api/enrollments/create/',
            json=enrollment_data,
            timeout=10
        )
        
        if response.status_code == 201:
            self.enrollment_status = 'created'
            self.save()
            return True
        else:
            self.enrollment_status = 'failed'
            self.notes = f"Erreur création inscription: {response.text}"
            self.save()
            return False
            
    except Exception as e:
        self.enrollment_status = 'failed'
        self.notes = f"Exception: {str(e)}"
        self.save()
        return False


class UserPaymentMethod(models.Model):
    """Méthodes de paiement enregistrées par l'utilisateur"""
    METHOD_CHOICES = [
        ('rib', 'RIB'),
        ('card', 'Carte bancaire'),
    ]
    
    # === CORRECTION : Ajoutez une clé primaire ===
    id = models.AutoField(primary_key=True, verbose_name='ID')
    
    user_id = models.IntegerField(
        verbose_name='ID Utilisateur'
    )
    method_type = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        verbose_name='Type de méthode'
    )
    
    # Pour RIB
    rib_number = models.CharField(
        max_length=27,
        verbose_name='Numéro RIB',
        blank=True,
        null=True
    )
    rib_holder_name = models.CharField(
        max_length=255,
        verbose_name='Titulaire',
        blank=True,
        null=True
    )
    rib_bank_name = models.CharField(
        max_length=100,
        verbose_name='Banque',
        blank=True,
        null=True
    )
    
    # Pour carte
    card_last_four = models.CharField(
        max_length=4,
        verbose_name='4 derniers chiffres',
        blank=True,
        null=True
    )
    card_expiry_month = models.CharField(
        max_length=2,
        verbose_name='Mois expiration',
        blank=True,
        null=True
    )
    card_expiry_year = models.CharField(
        max_length=4,
        verbose_name='Année expiration',
        blank=True,
        null=True
    )
    card_holder_name = models.CharField(
        max_length=255,
        verbose_name='Nom sur la carte',
        blank=True,
        null=True
    )
    card_type = models.CharField(
        max_length=20,
        verbose_name='Type de carte',
        blank=True,
        null=True
    )
    
    # Métadonnées
    is_default = models.BooleanField(
        default=False,
        verbose_name='Méthode par défaut'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Vérifiée'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date d\'ajout'
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Dernière utilisation'
    )
    
    class Meta:
        unique_together = ['user_id', 'rib_number']
        indexes = [
            models.Index(fields=['user_id', 'is_default']),
            models.Index(fields=['user_id', 'method_type']),
        ]
        verbose_name = 'Méthode de paiement'
        verbose_name_plural = 'Méthodes de paiement'
    
    def __str__(self):
        if self.method_type == 'rib':
            return f"RIB ****{self.rib_number[-4:] if self.rib_number else ''} - User {self.user_id}"
        else:
            return f"Carte ****{self.card_last_four} - User {self.user_id}"