# authentication/serializers.py - VERSION CORRIGÉE
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'user_type', 'date_naissance', 'telephone', 'date_joined',
            'is_superuser', 'is_staff', 'is_active',  # AJOUTEZ ces champs
            'photo_profil', 'pays', 'langue', 'bio',  # AJOUTEZ les nouveaux champs
            'website', 'linkedin', 'github', 'date_modification'
        ]
        read_only_fields = ['id', 'date_joined', 'date_modification']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                 'password', 'password2']  # SUPPRIMEZ 'user_type'
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        
        # Toujours créer un étudiant via l'API
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            # user_type='etudiant' sera défini automatiquement par le modèle
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Valide les identifiants et retourne l'utilisateur"""
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            # Essayer d'authentifier avec username
            user = authenticate(username=username, password=password)
            
            # Si échec, essayer avec email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Ce compte est désactivé.")
                
                # Retourner les données avec l'utilisateur
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError("Identifiants incorrects.")
        else:
            raise serializers.ValidationError("Les champs 'username' et 'password' sont obligatoires.")

class TokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()