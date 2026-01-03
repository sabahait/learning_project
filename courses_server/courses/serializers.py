# courses/serializers.py - VERSION ULTRA SIMPLE
from rest_framework import serializers
from .models import Course, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']

class CourseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'subtitle', 'description', 'short_description',
            'media_type', 'category', 'category_id', 
            'course_type', 'status', 'level',
            'objectives', 'prerequisites', 'target_audience',
            'price', 'discount_price', 'duration_hours', 'pages',
            'thumbnail', 'cover_photo', 'preview_video_url', 'document_file',
            'instructor_id', 'instructor_name',
            'language', 'tags', 'is_featured', 'certificate_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Ajoute des champs calculés"""
        data = super().to_representation(instance)
        # Ajouter le champ calculé is_discounted
        data['is_discounted'] = instance.is_discounted
        return data