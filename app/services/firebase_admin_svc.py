import os
import json
import threading
import firebase_admin
from firebase_admin import auth, credentials, firestore
from app.core.config import settings

# Controle de init único (thread-safe)
_admin_lock = threading.Lock()
_app_initialized = False


def _init_admin_if_needed():
    """Inicializa Firebase Admin uma única vez, com projectId explícito."""
    global _app_initialized
    
    if _app_initialized:
        return

    with _admin_lock:
        if _app_initialized:
            return

        print(f"\n{'='*60}")
        print(f"[FIREBASE] Inicializando Firebase Admin SDK...")
        print(f"{'='*60}")
        print(f"[FIREBASE] Project ID configurado: {settings.firebase_project_id}")
        
        cred = None
        cred_path = getattr(settings, "firebase_credentials_file", None)
        
        # OPÇÃO 1: Tenta carregar do arquivo JSON local
        if cred_path and os.path.exists(cred_path):
            print(f"[FIREBASE] ✅ Arquivo encontrado: {cred_path}")
            
            try:
                with open(cred_path, 'r') as f:
                    key_data = json.load(f)
                    json_project_id = key_data.get('project_id', 'NOT_FOUND')
                    json_client_email = key_data.get('client_email', 'NOT_FOUND')
                    
                    print(f"[FIREBASE] project_id no JSON: {json_project_id}")
                    print(f"[FIREBASE] client_email no JSON: {json_client_email}")
                    
                    if json_project_id != settings.firebase_project_id:
                        print(f"[FIREBASE] ⚠️  WARNING: project_id do JSON ({json_project_id}) != settings ({settings.firebase_project_id})")
                    else:
                        print(f"[FIREBASE] ✅ project_id confere!")
                
                cred = credentials.Certificate(cred_path)
                print(f"[FIREBASE] ✅ Credenciais carregadas do arquivo local")
                
            except Exception as e:
                print(f"[FIREBASE] ❌ ERRO ao ler arquivo JSON: {e}")
                raise
        
        # OPÇÃO 2: Tenta carregar do JSON completo em variável de ambiente
        elif settings.firebase_credentials_json:
            print(f"[FIREBASE] Arquivo local não encontrado")
            print(f"[FIREBASE] Tentando FIREBASE_CREDENTIALS_JSON...")
            
            try:
                key_data = json.loads(settings.firebase_credentials_json)
                json_project_id = key_data.get('project_id', 'NOT_FOUND')
                json_client_email = key_data.get('client_email', 'NOT_FOUND')
                
                print(f"[FIREBASE] project_id no JSON: {json_project_id}")
                print(f"[FIREBASE] client_email no JSON: {json_client_email}")
                
                if json_project_id != settings.firebase_project_id:
                    print(f"[FIREBASE] ⚠️  WARNING: project_id do JSON ({json_project_id}) != settings ({settings.firebase_project_id})")
                else:
                    print(f"[FIREBASE] ✅ project_id confere!")
                
                cred = credentials.Certificate(key_data)
                print(f"[FIREBASE] ✅ Credenciais carregadas do FIREBASE_CREDENTIALS_JSON (env)")
                
            except json.JSONDecodeError as e:
                print(f"[FIREBASE] ❌ ERRO: FIREBASE_CREDENTIALS_JSON não é um JSON válido!")
                print(f"[FIREBASE] Detalhes: {e}")
                raise Exception("FIREBASE_CREDENTIALS_JSON não é um JSON válido!")
            except Exception as e:
                print(f"[FIREBASE] ❌ ERRO ao processar FIREBASE_CREDENTIALS_JSON: {e}")
                raise
        
        # OPÇÃO 3: Tenta usar variáveis de ambiente individuais
        elif settings.firebase_private_key and settings.firebase_client_email:
            print(f"[FIREBASE] JSON não encontrado")
            print(f"[FIREBASE] Tentando variáveis individuais (FIREBASE_PRIVATE_KEY + FIREBASE_CLIENT_EMAIL)...")
            
            try:
                private_key = settings.firebase_private_key.replace("\\n", "\n")
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": settings.firebase_project_id,
                    "client_email": settings.firebase_client_email,
                    "private_key": private_key,
                })
                print(f"[FIREBASE] ✅ Credenciais carregadas de variáveis individuais")
                
            except Exception as e:
                print(f"[FIREBASE] ❌ ERRO ao criar credenciais: {e}")
                raise
        
        # NENHUMA OPÇÃO DISPONÍVEL
        else:
            print(f"\n[FIREBASE] ❌ NENHUMA CREDENCIAL CONFIGURADA!")
            print(f"\n[FIREBASE] Configure uma das opções abaixo:")
            print(f"  1️⃣  Arquivo local (desenvolvimento):")
            print(f"      FIREBASE_CREDENTIALS_FILE=/caminho/para/arquivo.json")
            print(f"\n  2️⃣  JSON completo em variável (produção - RECOMENDADO):")
            print(f"      FIREBASE_CREDENTIALS_JSON='{{\"type\":\"service_account\",...}}'")
            print(f"\n  3️⃣  Variáveis individuais (alternativa):")
            print(f"      FIREBASE_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----\\n...'")
            print(f"      FIREBASE_CLIENT_EMAIL='...@....iam.gserviceaccount.com'")
            print(f"\n{'='*60}\n")
            raise Exception("Nenhuma credencial Firebase configurada! Veja as opções acima.")

        # Inicializa o app com as opções
        options = {"projectId": settings.firebase_project_id}
        firebase_admin.initialize_app(cred, options)

        print(f"[FIREBASE] ✅ Firebase Admin SDK inicializado com sucesso!")
        print(f"[FIREBASE] Project ID ativo: {settings.firebase_project_id}")
        print(f"{'='*60}\n")
        
        _app_initialized = True


def verify_id_token(id_token: str) -> dict:
    """Verifica e decodifica o ID Token via Admin SDK."""
    _init_admin_if_needed()
    
    print(f"\n[VERIFY] Iniciando validação do token...")
    print(f"[VERIFY] Project ID esperado: {settings.firebase_project_id}")
    
    try:
        # Valida o token com folga de 60 segundos (para clock skew)
        decoded = auth.verify_id_token(id_token, clock_skew_seconds=60)
        
        print(f"[VERIFY] ✅ Token decodificado com sucesso!")
        print(f"[VERIFY] User ID: {decoded.get('user_id')}")
        print(f"[VERIFY] Email: {decoded.get('email')}")
        print(f"[VERIFY] Token aud (audience): {decoded.get('aud')}")
        print(f"[VERIFY] Token iss (issuer): {decoded.get('iss')}")
        
        # Validações adicionais
        aud = decoded.get("aud")
        iss = decoded.get("iss")
        
        if aud != settings.firebase_project_id:
            print(f"[VERIFY] ⚠️  WARNING: token.aud ({aud}) != settings.project ({settings.firebase_project_id})")
            print(f"[VERIFY] ❌ Token é de outro projeto Firebase!")
            raise Exception(f"Token audience mismatch: esperado '{settings.firebase_project_id}', recebido '{aud}'")
        
        expected_iss = f"https://securetoken.google.com/{settings.firebase_project_id}"
        if iss != expected_iss:
            print(f"[VERIFY] ⚠️  WARNING: token.iss ({iss}) != esperado ({expected_iss})")
            print(f"[VERIFY] ❌ Token issuer inválido!")
            raise Exception(f"Token issuer mismatch: esperado '{expected_iss}', recebido '{iss}'")
        
        print(f"[VERIFY] ✅ Todas as validações passaram!\n")
        return decoded
        
    except Exception as e:
        print(f"[VERIFY] ❌ ERRO na validação:")
        print(f"[VERIFY] Tipo: {type(e).__name__}")
        print(f"[VERIFY] Mensagem: {str(e)}\n")
        raise


def get_user(uid: str):
    """Obtém dados do usuário pelo UID."""
    _init_admin_if_needed()
    return auth.get_user(uid)


def set_custom_claims(uid: str, claims: dict):
    """Define custom claims para um usuário."""
    _init_admin_if_needed()
    auth.set_custom_user_claims(uid, claims)


def firestore_client():
    """Retorna o cliente Firestore."""
    _init_admin_if_needed()
    return firestore.client()


__all__ = [
    "_init_admin_if_needed",
    "verify_id_token",
    "get_user",
    "set_custom_claims",
    "firestore_client",
]
