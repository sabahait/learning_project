# payment_server/payments/views.py - VERSION COMPLÈTE
import requests
import json
import re
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction
from django.utils import timezone
from django.views.decorators.http import require_GET
from .models import PaymentTransaction, UserPaymentMethod
import uuid

@require_GET
def payment_home(request):
    """Page d'accueil du serveur de paiement"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Serveur de Paiement - Port 8003</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 20px;
                color: white;
            }
            .status {
                font-size: 1.5rem;
                margin-bottom: 30px;
                color: #d1d5db;
            }
            .endpoints {
                text-align: left;
                margin: 30px 0;
                padding: 20px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
            }
            .endpoint {
                margin: 10px 0;
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                font-family: 'Courier New', monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Serveur de Paiement</h1>
            <div class="status">✅ Opérationnel - Port 8003</div>
            
            <div class="endpoints">
                <h3>📡 Endpoints disponibles :</h3>
                <div class="endpoint">
                    <strong>POST</strong> /api/payment/process/ - Traiter un paiement
                </div>
                <div class="endpoint">
                    <strong>GET</strong> /api/payment/verify/&lt;user_id&gt;/&lt;course_id&gt;/ - Vérifier l'accès
                </div>
                <div class="endpoint">
                    <strong>GET</strong> /api/payment/history/&lt;user_id&gt;/ - Historique des paiements
                </div>
                <div class="endpoint">
                    <strong>GET</strong> /api/payment/methods/&lt;user_id&gt;/ - Méthodes de paiement enregistrées
                </div>
            </div>
            
            <div style="margin-top: 40px; padding: 20px; background: rgba(0, 255, 0, 0.1); border-radius: 10px;">
                <h3>🔗 Serveurs connectés :</h3>
                <p>Serveur Principal : <strong>http://127.0.0.1:8000</strong></p>
                <p>Serveur d'Authentification : <strong>http://127.0.0.1:8001</strong></p>
                <p>Serveur de Cours : <strong>http://127.0.0.1:8002</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

@csrf_exempt
def process_payment(request):
    """Traiter un paiement simulé"""
    print("=" * 60)
    print("💰 [process_payment] DÉBUT - Traitement d'un paiement")
    
    if request.method == 'POST':
        try:
            # Récupérer les données
            data = json.loads(request.body)
            print(f"📦 Données reçues: {data}")
            
            # Validation des données requises
            required_fields = ['user_id', 'course_id', 'course_name', 'amount']
            for field in required_fields:
                if field not in data:
                    print(f"❌ Champ manquant: {field}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Champ manquant: {field}'
                    }, status=400)
            
            user_id = int(data['user_id'])
            course_id = int(data['course_id'])
            course_name = data['course_name']
            amount = Decimal(str(data['amount']))
            
            print(f"🎯 Processus paiement:")
            print(f"   User ID: {user_id}")
            print(f"   Course ID: {course_id}")
            print(f"   Course: {course_name}")
            print(f"   Montant: {amount}€")
            
            # Validation du montant
            if amount < 0:
                print(f"❌ Montant invalide: {amount}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Montant invalide'
                }, status=400)
            
            # Si montant = 0, c'est un cours gratuit
            if amount == 0:
                print("🎓 Cours gratuit détecté")
                return process_free_course(user_id, course_id, course_name)
            
            # Validation des informations de paiement
            payment_method = data.get('payment_method', 'card')
            print(f"💳 Méthode de paiement: {payment_method}")
            
            if payment_method == 'card':
                # Validation carte (16 chiffres)
                card_number = data.get('card_number', '').replace(' ', '')
                if not re.match(r'^\d{16}$', card_number):
                    print(f"❌ Numéro de carte invalide: {card_number}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Numéro de carte invalide. Doit contenir 16 chiffres.'
                    }, status=400)
                
                # Validation date d'expiration
                expiry = data.get('card_expiry', '').replace(' ', '')
                if not re.match(r'^\d{2}/\d{2}$', expiry):
                    print(f"❌ Date d'expiration invalide: {expiry}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Date d\'expiration invalide. Format: MM/AA'
                    }, status=400)
                
                # Validation CVV
                cvv = data.get('card_cvv', '')
                if not re.match(r'^\d{3,4}$', cvv):
                    print(f"❌ CVV invalide: {cvv}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'CVV invalide. Doit contenir 3 ou 4 chiffres.'
                    }, status=400)
                
                card_holder = data.get('card_holder', '').strip()
                if not card_holder:
                    print(f"❌ Nom sur carte manquant")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Nom sur la carte requis'
                    }, status=400)
            
            else:
                print(f"❌ Méthode de paiement non supportée: {payment_method}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Méthode de paiement non supportée'
                }, status=400)
            
            # Processus de paiement dans une transaction
            with db_transaction.atomic():
                # 1. Créer la transaction
                transaction_data = {
                    'user_id': user_id,
                    'course_id': course_id,
                    'course_name': course_name,
                    'amount': amount,
                    'payment_method': payment_method,
                    'status': 'completed',  # Simulé donc toujours réussi
                }
                
                if payment_method == 'card':
                    transaction_data.update({
                        'card_last_four': card_number[-4:],
                        'card_expiry_month': expiry.split('/')[0],
                        'card_expiry_year': '20' + expiry.split('/')[1],
                        'card_holder_name': card_holder
                    })
                
                # Générer un code d'accès unique
                access_code = f"COURSE-{uuid.uuid4().hex[:8].upper()}"
                transaction_data['access_code'] = access_code
                
                transaction = PaymentTransaction.objects.create(**transaction_data)
                
                print(f"✅ Transaction créée: {transaction.id}")
                print(f"✅ Code d'accès: {access_code}")
                
                # 2. 🔐 Créer l'inscription sur le serveur de cours (8002)
                print(f"🌐 Tentative de création d'inscription sur serveur de cours...")
                
                try:
                    # Appeler le serveur de cours pour créer l'inscription
                    courses_response = requests.post(
                        f'http://127.0.0.1:8002/api/courses/{course_id}/enroll/',
                        json={
                            'user_id': user_id,
                            'course_id': course_id,
                            'access_code': access_code,
                            'payment_transaction_id': transaction.id
                        },
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if courses_response.status_code in [200, 201]:
                        print(f"✅ Inscription créée sur serveur de cours")
                        transaction.enrollment_status = 'created'
                        transaction.save()
                        
                        # 3. Enregistrer la méthode de paiement pour l'utilisateur
                        save_payment_method = data.get('save_payment_method', False)
                        if save_payment_method:
                            save_user_payment_method(user_id, payment_method, data)
                        
                        return JsonResponse({
                            'status': 'success',
                            'transaction_id': transaction.id,
                            'access_code': access_code,
                            'message': 'Paiement réussi et cours débloqué',
                            'details': {
                                'course_name': course_name,
                                'amount': float(amount),
                                'payment_method': payment_method,
                                'access_code': access_code,
                                'transaction_date': timezone.now().isoformat()
                            }
                        })
                    else:
                        print(f"❌ Échec création inscription: {courses_response.status_code}")
                        transaction.enrollment_status = 'failed'
                        transaction.save()
                        
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Paiement réussi mais échec de déblocage du cours',
                            'transaction_id': transaction.id,
                            'access_code': access_code
                        }, status=500)
                        
                except requests.exceptions.ConnectionError:
                    print(f"❌ Serveur de cours inaccessible")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Serveur de cours inaccessible',
                        'transaction_id': transaction.id,
                        'access_code': access_code
                    }, status=503)
                
        except json.JSONDecodeError:
            print(f"❌ Format JSON invalide")
            return JsonResponse({
                'status': 'error',
                'message': 'Format JSON invalide'
            }, status=400)
        except ValueError as e:
            print(f"❌ Valeur invalide: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'Données invalides: {str(e)}'
            }, status=400)
        except Exception as e:
            print(f"💥 Erreur lors du paiement: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur interne: {str(e)}'
            }, status=500)
    else:
        print(f"❌ Méthode non autorisée: {request.method}")
        return JsonResponse({
            'status': 'error',
            'message': 'Méthode non autorisée'
        }, status=405)

def process_free_course(user_id, course_id, course_name):
    """Traiter un cours gratuit"""
    print(f"🎓 [process_free_course] Cours gratuit pour user {user_id}, cours {course_id}")
    
    try:
        with db_transaction.atomic():
            # Créer une transaction avec montant 0
            access_code = f"FREE-{uuid.uuid4().hex[:8].upper()}"
            
            transaction = PaymentTransaction.objects.create(
                user_id=user_id,
                course_id=course_id,
                course_name=course_name,
                amount=0,
                payment_method='free',
                status='completed',
                access_code=access_code,
                enrollment_status='pending'
            )
            
            print(f"✅ Cours gratuit - Transaction: {transaction.id}")
            
            # Créer l'inscription sur le serveur de cours
            try:
                courses_response = requests.post(
                    f'http://127.0.0.1:8002/api/courses/{course_id}/enroll/',
                    json={
                        'user_id': user_id,
                        'course_id': course_id,
                        'access_code': access_code,
                        'is_free': True
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if courses_response.status_code in [200, 201]:
                    transaction.enrollment_status = 'created'
                    transaction.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'transaction_id': transaction.id,
                        'access_code': access_code,
                        'message': 'Cours gratuit ajouté à votre compte',
                        'details': {
                            'course_name': course_name,
                            'amount': 0,
                            'payment_method': 'free',
                            'access_code': access_code
                        }
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Erreur lors de l\'ajout du cours gratuit',
                        'transaction_id': transaction.id
                    }, status=500)
                    
            except requests.exceptions.ConnectionError:
                print(f"❌ Serveur de cours inaccessible pour cours gratuit")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Serveur de cours inaccessible',
                    'transaction_id': transaction.id,
                    'access_code': access_code
                }, status=503)
                
    except Exception as e:
        print(f"💥 Erreur cours gratuit: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur: {str(e)}'
        }, status=500)

def save_user_payment_method(user_id, method_type, payment_data):
    """Enregistrer une méthode de paiement pour l'utilisateur"""
    try:
        if method_type == 'card':
            card_number = payment_data.get('card_number', '').replace(' ', '')
            UserPaymentMethod.objects.update_or_create(
                user_id=user_id,
                method_type='card',
                card_last_four=card_number[-4:],
                defaults={
                    'method_type': 'card',
                    'card_expiry_month': payment_data.get('card_expiry', '').split('/')[0],
                    'card_expiry_year': '20' + payment_data.get('card_expiry', '').split('/')[1],
                    'card_holder_name': payment_data.get('card_holder'),
                    'is_default': True,
                    'last_used': timezone.now()
                }
            )
        print(f"✅ Méthode de paiement enregistrée pour user {user_id}")
    except Exception as e:
        print(f"⚠️ Erreur enregistrement méthode paiement: {e}")

@csrf_exempt
def verify_course_access(request, user_id, course_id):
    """Vérifier si un utilisateur a accès à un cours"""
    print(f"🔍 [verify_course_access] Vérification user {user_id}, cours {course_id}")
    
    try:
        user_id = int(user_id)
        course_id = int(course_id)
        
        # Vérifier les transactions complétées
        transaction = PaymentTransaction.objects.filter(
            user_id=user_id,
            course_id=course_id,
            status='completed'
        ).first()
        
        if transaction:
            print(f"✅ Accès autorisé pour user {user_id} au cours {course_id}")
            return JsonResponse({
                'has_access': True,
                'access_code': transaction.access_code,
                'transaction_id': transaction.id,
                'payment_method': transaction.payment_method,
                'purchased_at': transaction.created_at.strftime('%d/%m/%Y %H:%M'),
                'course_name': transaction.course_name
            })
        
        print(f"❌ Pas d'accès pour user {user_id} au cours {course_id}")
        return JsonResponse({
            'has_access': False,
            'message': 'Accès non autorisé. Ce cours nécessite un achat.',
            'suggested_action': 'purchase'
        })
        
    except Exception as e:
        print(f"💥 Erreur vérification accès: {e}")
        return JsonResponse({
            'has_access': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def get_user_payment_history(request, user_id):
    """Récupérer l'historique des paiements d'un utilisateur"""
    print(f"📜 [get_user_payment_history] Historique pour user {user_id}")
    
    try:
        user_id = int(user_id)
        
        transactions = PaymentTransaction.objects.filter(
            user_id=user_id
        ).order_by('-created_at')
        
        history = []
        for t in transactions:
            history.append({
                'transaction_id': t.id,
                'course_id': t.course_id,
                'course_name': t.course_name,
                'amount': float(t.amount),
                'payment_method': t.payment_method,
                'status': t.status,
                'access_code': t.access_code,
                'date': t.created_at.strftime('%d/%m/%Y %H:%M'),
                'enrollment_status': t.enrollment_status
            })
        
        print(f"✅ {len(history)} transactions trouvées")
        
        return JsonResponse({
            'status': 'success',
            'user_id': user_id,
            'total_transactions': len(history),
            'total_spent': float(sum(t.amount for t in transactions if t.status == 'completed')),
            'transactions': history
        })
        
    except Exception as e:
        print(f"💥 Erreur historique paiement: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def get_saved_payment_methods(request, user_id):
    """Récupérer les méthodes de paiement enregistrées d'un utilisateur"""
    print(f"💳 [get_saved_payment_methods] Méthodes pour user {user_id}")
    
    try:
        user_id = int(user_id)
        
        # Récupérer toutes les méthodes de paiement de l'utilisateur
        payment_methods = UserPaymentMethod.objects.filter(user_id=user_id).order_by('-is_default', '-last_used')
        
        methods_list = []
        for method in payment_methods:
            method_data = {
                'id': method.id,
                'method_type': method.method_type,
                'display_name': method.get_display_name(),
                'is_default': method.is_default,
                'last_used': method.last_used.strftime('%d/%m/%Y %H:%M') if method.last_used else None,
                'created_at': method.created_at.strftime('%d/%m/%Y') if method.created_at else None
            }
            
            # Ajouter les détails spécifiques selon le type
            if method.method_type == 'card':
                method_data.update({
                    'card_last_four': method.card_last_four,
                    'card_expiry': f"{method.card_expiry_month}/{method.card_expiry_year[-2:]}",
                    'card_holder': method.card_holder_name
                })
            
            methods_list.append(method_data)
        
        print(f"✅ {len(methods_list)} méthodes trouvées")
        
        return JsonResponse({
            'status': 'success',
            'user_id': user_id,
            'payment_methods': methods_list,
            'count': len(methods_list),
            'has_methods': len(methods_list) > 0
        })
        
    except Exception as e:
        print(f"💥 Erreur récupération méthodes paiement: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur: {str(e)}'
        }, status=500)