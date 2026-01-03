# create_categories.py
import os
import django
import sys

# Configure Django
sys.path.append('C:\\Users\\pc\\Desktop\\learning_project\\courses_server')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'courses_server.settings')
django.setup()

from courses.models import Category
from django.utils.text import slugify

def create_default_categories():
    categories_data = [
        {
            'id': 1,
            'name': 'Développement Web',
            'description': 'Cours de développement web (HTML, CSS, JavaScript, frameworks)'
        },
        {
            'id': 2,
            'name': 'Data Science',
            'description': 'Data science, machine learning, intelligence artificielle'
        },
        {
            'id': 3,
            'name': 'Mobile Development',
            'description': 'Développement d\'applications mobiles'
        },
        {
            'id': 4,
            'name': 'Design UI/UX',
            'description': 'Design d\'interface et expérience utilisateur'
        },
        {
            'id': 5,
            'name': 'Business',
            'description': 'Business, management et entrepreneuriat'
        },
        {
            'id': 6,
            'name': 'Marketing Digital',
            'description': 'Marketing en ligne et réseaux sociaux'
        },
        {
            'id': 7,
            'name': 'Programmation',
            'description': 'Bases de la programmation et algorithmes'
        },
        {
            'id': 8,
            'name': 'Base de Données',
            'description': 'Administration et conception de bases de données'
        },
        {
            'id': 9,
            'name': 'DevOps',
            'description': 'DevOps, déploiement et infrastructure'
        },
        {
            'id': 10,
            'name': 'Cybersécurité',
            'description': 'Sécurité informatique et protection des données'
        }
    ]
    
    created_count = 0
    for cat_data in categories_data:
        # Créer le slug à partir du nom
        slug = slugify(cat_data['name'])
        
        # Vérifier si la catégorie existe déjà
        category, created = Category.objects.get_or_create(
            id=cat_data['id'],
            defaults={
                'name': cat_data['name'],
                'slug': slug,
                'description': cat_data['description']
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Catégorie créée : {cat_data['name']}")
        else:
            print(f"ℹ️ Catégorie existante : {cat_data['name']}")
    
    print(f"\n✅ {created_count} catégories créées sur {len(categories_data)}")

if __name__ == '__main__':
    print("Création des catégories par défaut...")
    create_default_categories()