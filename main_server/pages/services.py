# pages/services.py - VERSION CORRIGÉE

import requests
import json
from django.conf import settings

class AuthService:
    """Service pour communiquer avec le serveur d'authentification"""
    
    @staticmethod
    def verify_token(token):
        """Vérifie un token JWT avec le serveur auth"""
        if not token:
            print("❌ [verify_token] Token vide")
            return False, None
            
        try:
            print(f"🔐 [verify_token] Vérification token longueur: {len(token)}")
            print(f"🔐 [verify_token] Token début: {token[:50]}...")
            
            # URL de vérification
            verify_url = f"{settings.AUTH_SERVICE_URL}/api/auth/verify/"
            print(f"🌐 [verify_token] URL: {verify_url}")
            
            # Envoyer la requête
            response = requests.post(
                verify_url,
                json={'token': token},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📡 [verify_token] Réponse status: {response.status_code}")
            print(f"📡 [verify_token] Réponse texte: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ [verify_token] Données reçues: {data}")
                valid = data.get('valid', False)
                user_data = data.get('user', {})
                print(f"✅ [verify_token] Token valide: {valid}, User: {user_data.get('username', 'N/A')}")
                return valid, user_data
            else:
                print(f"❌ [verify_token] Erreur HTTP: {response.status_code}")
                # Essayer avec GET si POST échoue
                try:
                    print("🔄 [verify_token] Essai avec GET...")
                    get_response = requests.get(
                        f"{settings.AUTH_SERVICE_URL}/api/verify-token/",
                        headers={'Authorization': f'Bearer {token}'},
                        timeout=10
                    )
                    print(f"📡 [verify_token] GET réponse: {get_response.status_code}")
                    if get_response.status_code == 200:
                        get_data = get_response.json()
                        print(f"✅ [verify_token] GET données: {get_data}")
                        return True, get_data
                except Exception as get_error:
                    print(f"❌ [verify_token] GET échoué: {get_error}")
                
                return False, None
                
        except requests.exceptions.ConnectionError:
            print("❌ [verify_token] Serveur auth inaccessible")
            return False, None
        except Exception as e:
            print(f"💥 [verify_token] Exception: {e}")
            import traceback
            traceback.print_exc()
            return False, None

class CoursesService:
    """Service pour communiquer avec le serveur de cours"""
    
    @staticmethod
    def create_course_with_files(course_data, cover_photo=None, document_file=None, token=None):
        """Crée un nouveau cours avec fichiers (FormData)"""
        try:
            print(f"📤 Envoi cours avec fichiers à {settings.COURSES_SERVICE_URL}/api/courses/")
            print(f"   Token: {token[:30]}..." if token else "❌ Pas de token")
            
            # Préparer les données multipart
            files = {}
            data = {}
            
            # Ajouter les fichiers s'ils existent
            if cover_photo:
                files['cover_photo'] = (cover_photo.name, cover_photo, cover_photo.content_type)
                print(f"📁 Cover photo: {cover_photo.name} ({cover_photo.size} bytes)")
            
            if document_file:
                files['document_file'] = (document_file.name, document_file, document_file.content_type)
                print(f"📁 Document file: {document_file.name} ({document_file.size} bytes)")
            
            # Ajouter les autres données
            for key, value in course_data.items():
                if value is not None:
                    data[key] = str(value)
            
            print(f"📦 Données texte: {json.dumps(data, indent=2)}")
            print(f"📁 Fichiers à envoyer: {list(files.keys())}")
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            # Envoyer la requête
            response = requests.post(
                f"{settings.COURSES_SERVICE_URL}/api/courses/",
                data=data,
                files=files if files else None,
                headers=headers,
                timeout=30
            )
            
            print(f"📡 Réponse serveur cours: {response.status_code}")
            print(f"   Contenu: {response.text[:500]}")
            
            if response.status_code == 201:
                response_data = response.json()
                print(f"✅ Cours créé avec succès! ID: {response_data.get('id', 'N/A')}")
                return True, response_data
            else:
                error_msg = f'Erreur {response.status_code}'
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                    
                    # Afficher les détails d'erreur spécifiques
                    if 'cover_photo' in error_data:
                        error_msg = f"Erreur cover_photo: {error_data['cover_photo']}"
                    elif 'detail' in error_data:
                        error_msg = error_data['detail']
                    elif 'non_field_errors' in error_data:
                        error_msg = f"Erreurs: {error_data['non_field_errors']}"
                        
                except json.JSONDecodeError:
                    error_msg = response.text[:200]
                    
                print(f"❌ Erreur création cours: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.ConnectionError:
            error_msg = "Serveur de cours inaccessible"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            print(f"💥 {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    @staticmethod
    def create_course(course_data, token):
        """Crée un nouveau cours sans fichiers (pour API JSON)"""
        try:
            print(f"📤 Envoi cours (JSON) à {settings.COURSES_SERVICE_URL}/api/courses/")
            print(f"   Token: {token[:30]}...")
            
            response = requests.post(
                f"{settings.COURSES_SERVICE_URL}/api/courses/",
                json=course_data,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                timeout=15
            )
            
            print(f"📡 Réponse serveur cours: {response.status_code}")
            print(f"   Contenu: {response.text[:200]}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Cours créé: {data.get('id', 'N/A')}")
                return True, data
            else:
                error_msg = f'Erreur {response.status_code}'
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                    if 'detail' in error_data:
                        error_msg = error_data['detail']
                except:
                    pass
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.ConnectionError:
            error_msg = "Serveur de cours inaccessible"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Erreur: {str(e)}"
            print(f"💥 {error_msg}")
            return False, error_msg
    
    @staticmethod
    def get_all_courses(token):
        """Récupère tous les cours depuis courses server - VERSION CORRIGÉE"""
        try:
            print(f"📡 [get_all_courses] Appel API cours avec token: {token[:30]}...")
            
            response = requests.get(
                f"{settings.COURSES_SERVICE_URL}/api/courses/",
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            
            print(f"📡 [get_all_courses] Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ [get_all_courses] Type données: {type(data)}")
                
                # CORRECTION ICI : Gérer selon le type de données
                if isinstance(data, list):
                    # Le serveur retourne directement une liste de cours
                    print(f"✅ Format liste: {len(data)} cours")
                    return data
                elif isinstance(data, dict):
                    # Le serveur retourne un dict avec clé 'courses'
                    if 'courses' in data:
                        print(f"✅ Format dict avec 'courses': {len(data['courses'])} cours")
                        return data['courses']
                    else:
                        print(f"⚠️ Dict sans clé 'courses', clés: {list(data.keys())}")
                        return []
                else:
                    print(f"⚠️ Format inattendu: {type(data)}")
                    return []
            else:
                print(f"❌ [get_all_courses] Erreur HTTP: {response.status_code}")
                print(f"❌ [get_all_courses] Message: {response.text[:200]}")
                return []
                
        except requests.RequestException as e:
            print(f"❌ [get_all_courses] Erreur connexion: {e}")
            return []
        except Exception as e:
            print(f"💥 [get_all_courses] Erreur inattendue: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_categories(token):
        """Récupère les catégories depuis courses server"""
        try:
            response = requests.get(
                f"{settings.COURSES_SERVICE_URL}/api/categories/",
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Retourner sous forme de liste simple d'objets {id, name}
                categories = []
                
                # Si la réponse est une liste
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            categories.append({
                                'id': item.get('id'),
                                'name': item.get('name', item.get('title', 'Sans nom'))
                            })
                        else:
                            categories.append({'id': len(categories) + 1, 'name': str(item)})
                # Si la réponse est un dict avec une clé 'categories'
                elif isinstance(data, dict) and 'categories' in data:
                    for item in data['categories']:
                        if isinstance(item, dict):
                            categories.append({
                                'id': item.get('id'),
                                'name': item.get('name', item.get('title', 'Sans nom'))
                            })
                        else:
                            categories.append({'id': len(categories) + 1, 'name': str(item)})
                # Si la réponse est un dict direct
                elif isinstance(data, dict) and 'id' in data:
                    categories.append({
                        'id': data.get('id'),
                        'name': data.get('name', 'Catégorie')
                    })
                
                return categories
            else:
                print(f"Erreur serveur: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            print(f"Erreur récupération catégories: {e}")
            return []
    
    @staticmethod
    def delete_course(course_id, token):
        """Supprimer un cours"""
        try:
            print(f"🗑️ Suppression cours ID {course_id}")
            print(f"   Token: {token[:30]}...")
            
            response = requests.delete(
                f"{settings.COURSES_SERVICE_URL}/api/courses/{course_id}/",
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            
            print(f"📡 Réponse suppression: {response.status_code}")
            
            if response.status_code == 204:
                return True, 'Course deleted successfully'
            else:
                error_msg = f'Error {response.status_code}'
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                return False, error_msg
                
        except Exception as e:
            print(f"Error deleting course: {e}")
            return False, str(e)
    
    @staticmethod
    def update_course(course_id, course_data, token):
        """Modifier un cours (sans fichiers)"""
        try:
            print(f"📤 Modification cours ID {course_id} (JSON) à {settings.COURSES_SERVICE_URL}/api/courses/{course_id}/")
            print(f"   Token: {token[:30]}...")
            
            response = requests.put(
                f"{settings.COURSES_SERVICE_URL}/api/courses/{course_id}/",
                json=course_data,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                timeout=15
            )
            
            print(f"📡 Réponse serveur cours: {response.status_code}")
            print(f"   Contenu: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Cours modifié: {data.get('id', 'N/A')}")
                return True, data
            else:
                error_msg = f'Erreur {response.status_code}'
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                    if 'detail' in error_data:
                        error_msg = error_data['detail']
                except:
                    pass
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.ConnectionError:
            error_msg = "Serveur de cours inaccessible"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Erreur: {str(e)}"
            print(f"💥 {error_msg}")
            return False, error_msg
    
    @staticmethod
    def get_courses(token):
        """Récupère les cours depuis le serveur de cours - Alternative"""
        try:
            courses_service_url = settings.COURSES_SERVICE_URL.rstrip('/')
            url = f"{courses_service_url}/api/courses/"
            
            print(f"📡 [CoursesService.get_courses] Récupération depuis: {url}")
            print(f"   Token: {token[:30]}..." if token else "❌ Pas de token")
            
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            print(f"📡 [CoursesService.get_courses] Réponse: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ [CoursesService.get_courses] Type données reçues: {type(data)}")
                
                # Gérer différents formats de réponse
                courses = []
                
                if isinstance(data, list):
                    # Format 1: Liste directe
                    courses = data
                    print(f"✅ Format: Liste directe ({len(courses)} cours)")
                    
                elif isinstance(data, dict):
                    # Format 2: Dict avec clé 'courses'
                    if 'courses' in data:
                        courses = data['courses']
                        print(f"✅ Format: Dict avec clé 'courses' ({len(courses)} cours)")
                    
                    # Format 3: Dict avec pagination (Django REST)
                    elif 'results' in data:
                        courses = data['results']
                        print(f"✅ Format: Pagination Django REST ({len(courses)} cours)")
                        
                    # Format 4: Dict unique
                    elif 'id' in data:
                        courses = [data]
                        print(f"✅ Format: Dict unique (1 cours)")
                        
                    else:
                        # Essayer d'extraire les cours autrement
                        print(f"⚠️ Format inattendu, clés disponibles: {list(data.keys())}")
                        
                        # Chercher une clé qui contient une liste
                        for key, value in data.items():
                            if isinstance(value, list):
                                courses = value
                                print(f"✅ Trouvé cours dans clé '{key}' ({len(courses)} cours)")
                                break
                                
                        if not courses:
                            # Considérer tout le dict comme un cours
                            courses = [data]
                            print(f"⚠️ Considéré comme cours unique")
                
                print(f"✅ Total cours récupérés: {len(courses)}")
                
                # Debug: afficher les premiers cours
                if courses and len(courses) > 0:
                    print(f"📋 Premier cours:")
                    first_course = courses[0]
                    print(f"   ID: {first_course.get('id', 'N/A')}")
                    print(f"   Titre: {first_course.get('title', 'N/A')}")
                    print(f"   Catégorie: {first_course.get('category', 'N/A')}")
                    
                return True, courses
                
            elif response.status_code == 401:
                print("❌ [CoursesService.get_courses] Token invalide ou expiré")
                return False, "Token invalide ou expiré"
                
            elif response.status_code == 403:
                print("❌ [CoursesService.get_courses] Accès non autorisé")
                return False, "Accès non autorisé"
                
            else:
                print(f"❌ [CoursesService.get_courses] Erreur {response.status_code}: {response.text[:200]}")
                return False, f"Erreur {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            error_msg = "Serveur de cours inaccessible"
            print(f"❌ [CoursesService.get_courses] {error_msg}")
            return False, error_msg
            
        except requests.exceptions.Timeout:
            error_msg = "Timeout lors de la connexion au serveur de cours"
            print(f"❌ [CoursesService.get_courses] {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            print(f"💥 [CoursesService.get_courses] {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    @staticmethod
    def update_course_with_files(course_id, course_data, cover_photo=None, document_file=None, token=None):
        """Modifier un cours avec fichiers (FormData)"""
        try:
            print(f"📤 Modification cours ID {course_id} avec fichiers à {settings.COURSES_SERVICE_URL}/api/courses/{course_id}/")
            print(f"   Token: {token[:30]}..." if token else "❌ Pas de token")
            
            # Préparer les données multipart
            files = {}
            data = {}
            
            # Ajouter les fichiers s'ils existent
            if cover_photo:
                files['cover_photo'] = (cover_photo.name, cover_photo, cover_photo.content_type)
                print(f"📁 Nouvelle cover photo: {cover_photo.name} ({cover_photo.size} bytes)")
            
            if document_file:
                files['document_file'] = (document_file.name, document_file, document_file.content_type)
                print(f"📁 Nouveau document file: {document_file.name} ({document_file.size} bytes)")
            
            # Ajouter les autres données
            for key, value in course_data.items():
                if value is not None:
                    data[key] = str(value)
            
            print(f"📦 Données texte: {json.dumps(data, indent=2)}")
            print(f"📁 Fichiers à envoyer: {list(files.keys())}")
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            # Essayer d'abord avec PUT, sinon avec PATCH
            methods_to_try = ['PUT', 'PATCH']
            
            for method in methods_to_try:
                print(f"🔄 Essai avec méthode {method}...")
                try:
                    if method == 'PUT':
                        response = requests.put(
                            f"{settings.COURSES_SERVICE_URL}/api/courses/{course_id}/",
                            data=data,
                            files=files if files else None,
                            headers=headers,
                            timeout=30
                        )
                    else:  # PATCH
                        response = requests.patch(
                            f"{settings.COURSES_SERVICE_URL}/api/courses/{course_id}/",
                            data=data,
                            files=files if files else None,
                            headers=headers,
                            timeout=30
                        )
                    
                    print(f"📡 Réponse serveur cours ({method}): {response.status_code}")
                    print(f"   Contenu: {response.text[:500]}")
                    
                    if response.status_code in [200, 201]:
                        response_data = response.json()
                        print(f"✅ Cours modifié avec succès! ID: {response_data.get('id', 'N/A')}")
                        return True, response_data
                    elif response.status_code == 404:
                        error_msg = f'Cours ID {course_id} non trouvé'
                        print(f"❌ {error_msg}")
                        return False, error_msg
                    else:
                        # Continuer avec la méthode suivante
                        continue
                        
                except requests.exceptions.ConnectionError:
                    error_msg = "Serveur de cours inaccessible"
                    print(f"❌ {error_msg}")
                    return False, error_msg
                except Exception as e:
                    print(f"⚠️ Erreur avec {method}: {str(e)}")
                    continue
            
            # Si aucune méthode n'a fonctionné
            error_msg = f'Erreur lors de la modification du cours'
            print(f"❌ {error_msg}")
            
            # Essayer de récupérer le message d'erreur
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
                
                if 'cover_photo' in error_data:
                    error_msg = f"Erreur cover_photo: {error_data['cover_photo']}"
                elif 'detail' in error_data:
                    error_msg = error_data['detail']
                elif 'non_field_errors' in error_data:
                    error_msg = f"Erreurs: {error_data['non_field_errors']}"
                    
            except:
                error_msg = response.text[:200] if 'response' in locals() else error_msg
                
            return False, error_msg
                
        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            print(f"💥 {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg