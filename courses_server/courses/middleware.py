# courses/middleware.py ou où se trouve votre middleware
class CoursesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        print(f"🔐 [CoursesMiddleware] Path: {request.path}")
        
        # LISTE DES PATHS PUBLICS (sans authentification)
        PUBLIC_PATHS = [
            '/api/courses/',           # Liste des cours
            '/api/categories/',        # Liste des catégories
            '/api/health/',            # Health check
            '/api/status/',            # Status
            '/favicon.ico',            # Favicon
            '/static/',                # Fichiers statiques
            '/media/',                 # Fichiers média
        ]
        
        # Vérifier si le path est public
        is_public_path = any(request.path.startswith(path) for path in PUBLIC_PATHS)
        
        if is_public_path:
            print(f"✅ [CoursesMiddleware] Path public autorisé: {request.path}")
            # Pour les paths publics, on autorise sans vérification
            request.user_data = {'is_public': True}
            return self.get_response(request)
        
        # Pour les autres paths, vérifier l'authentification
        auth_header = request.headers.get('Authorization')
        print(f"🔐 [CoursesMiddleware] Auth header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            print(f"❌ [CoursesMiddleware] No valid Authorization header")
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Vérifier le token auprès de auth_server
            response = requests.get(
                f'{settings.AUTH_SERVICE_URL}/api/verify-token/',
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ [CoursesMiddleware] User authenticated: {user_data.get('username')}")
                request.user_data = user_data
                return self.get_response(request)
            else:
                print(f"❌ [CoursesMiddleware] Token invalid")
                return JsonResponse({'error': 'Invalid token'}, status=403)
                
        except requests.RequestException as e:
            print(f"❌ [CoursesMiddleware] Auth server error: {e}")
            return JsonResponse({'error': 'Authentication service unavailable'}, status=503)