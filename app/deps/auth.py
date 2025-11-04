from typing import Optional
from fastapi import Security, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.firebase_admin_svc import verify_id_token
import traceback

bearer = HTTPBearer(auto_error=False)

def firebase_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer),
    authorization: Optional[str] = Header(default=None),
):
    """
    Valida o token Firebase e retorna os dados do usuário.
    Aceita Authorization: Bearer <id_token>
    """
    token = None
    
    # Tenta pegar o token do HTTPBearer primeiro
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        print(f"[AUTH] Token recebido via HTTPBearer")
    # Fallback para o header Authorization direto
    elif authorization:
        parts = authorization.split()
        if len(parts) >= 2 and parts[0].lower() == "bearer":
            token = parts[1]
            print(f"[AUTH] Token recebido via Header direto")

    if not token:
        print(f"[AUTH] ❌ Nenhum token fornecido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forneça Authorization: Bearer <id_token>."
        )

    # Log dos primeiros caracteres do token (para debug sem expor o token completo)
    print(f"[AUTH] Token recebido (primeiros 50 chars): {token[:50]}...")
    print(f"[AUTH] Tamanho do token: {len(token)} caracteres")
    
    try:
        # Tenta validar o token
        result = verify_id_token(token)
        user_id = result.get('user_id', 'UNKNOWN')
        email = result.get('email', 'UNKNOWN')
        print(f"[AUTH] ✅ Token válido!")
        print(f"[AUTH] User ID: {user_id}")
        print(f"[AUTH] Email: {email}")
        return result
        
    except Exception as e:
        # Log detalhado do erro
        print(f"[AUTH] ❌ ERRO ao validar token:")
        print(f"[AUTH] Tipo de erro: {type(e).__name__}")
        print(f"[AUTH] Mensagem: {str(e)}")
        print(f"[AUTH] Stacktrace completo:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado."
        )