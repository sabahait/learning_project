# authentication/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'})
    )
    
    # SUPPRIMEZ le champ user_type complètement
    # Ne mettez pas de champ user_type dans le formulaire
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les messages d'aide
        self.fields['password1'].help_text = """
            Votre mot de passe doit contenir au moins 8 caractères.
            Évitez les mots de passe trop courants ou entièrement numériques.
        """
        self.fields['password2'].help_text = 'Entrez le même mot de passe que précédemment, pour vérification.'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Un utilisateur avec cet email existe déjà.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        # IMPORTANT: Toujours étudiant pour les inscriptions via formulaire
        user.is_superuser = False
        user.is_staff = False
        user.user_type = 'etudiant'  # Forcé à étudiant
        
        if commit:
            user.save()
        return user

# authentication/forms.py (suite)
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 
            'date_naissance', 'telephone', 'photo_profil',
            'pays', 'langue', 'bio', 'website', 
            'linkedin', 'github'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+212 6...'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Parlez-nous de vous...'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/...'}),
            'github': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/...'}),
            'pays': forms.Select(attrs={'class': 'form-control'}),
            'langue': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            # Vérifier que l'email n'est pas utilisé par un autre utilisateur
            qs = User.objects.filter(email=email)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Cet email est déjà utilisé par un autre utilisateur.")
        return email
    
    def clean_date_naissance(self):
        date_naissance = self.cleaned_data.get('date_naissance')
        if date_naissance:
            from datetime import date
            today = date.today()
            age = today.year - date_naissance.year - ((today.month, today.day) < (date_naissance.month, date_naissance.day))
            if age < 13:
                raise forms.ValidationError("Vous devez avoir au moins 13 ans.")
            if age > 120:
                raise forms.ValidationError("Veuillez vérifier votre date de naissance.")
        return date_naissance

class AdminUserUpdateForm(ProfileUpdateForm):
    """Formulaire pour les admins pour mettre à jour n'importe quel utilisateur"""
    is_superuser = forms.BooleanField(
        required=False,
        label='Administrateur système',
        help_text='Donne tous les droits sans restriction'
    )
    is_staff = forms.BooleanField(
        required=False,
        label='Accès à l\'interface admin',
        help_text='Permet d\'accéder à l\'interface d\'administration Django'
    )
    is_active = forms.BooleanField(
        required=False,
        label='Compte actif',
        help_text='Désactiver pour bloquer la connexion'
    )
    
    class Meta(ProfileUpdateForm.Meta):
        fields = ProfileUpdateForm.Meta.fields + ['is_superuser', 'is_staff', 'is_active']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Mettre à jour le user_type en fonction de is_superuser
        if self.cleaned_data.get('is_superuser'):
            user.user_type = 'admin'
        else:
            user.user_type = 'etudiant'
        
        if commit:
            user.save()
        return user