from fastapi import APIRouter, HTTPException, Depends
from app.models.user import RegisterIn, LoginIn, TokenOut
from app.services.firebase_identity_svc import signup_email_password, signin_email_password, refresh_id_token
from app.deps.auth import firebase_current_user
from app.services.coins_service import coins_service
from app.services import firebase_identity_svc

# ============================================
# CORREÇÃO 1: prefix="/auth/auth" 
# para ter /auth/auth/register
# ============================================
router = APIRouter(prefix="/auth/auth", tags=["Auth", "auth"])


@router.get("/verify")
def verify(user = Depends(firebase_current_user)):
    """
    Endpoint: GET /auth/auth/verify
    """
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
        "aud": user.get("aud"),
        "iss": user.get("iss"),
    }


# ============================================
# CORREÇÃO 2: Manter apenas UM endpoint /register
# Combinei os dois em um só
# ============================================
@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn):
    """
    Register a new user
    
    Endpoint: POST /auth/auth/register
    """
    try:
        # Registra o usuário no Firebase
        data = await signup_email_password(body.email, body.password)
        
        local_id = data["localId"]
        
        # Inicializa moedas para o novo usuário
        await coins_service.initialize_user_coins(local_id)
        
        # Retorna os tokens
        return {
            "id_token": data["idToken"],
            "refresh_token": data["refreshToken"],
            "expires_in": int(data["expiresIn"]),
            "local_id": local_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registro falhou: {str(e)}")


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn):
    """
    Login a user
    
    Endpoint: POST /auth/auth/login
    """
    try:
        data = await signin_email_password(body.email, body.password)
        return {
            "id_token": data["idToken"],
            "refresh_token": data["refreshToken"],
            "expires_in": int(data["expiresIn"]),
            "local_id": data["localId"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login falhou: {str(e)}")


@router.post("/refresh", response_model=TokenOut)
async def refresh(refresh_token: str):
    """
    Refresh token
    
    Endpoint: POST /auth/auth/refresh
    """
    try:
        data = await refresh_id_token(refresh_token)
        # resposta do securetoken usa chaves diferentes:
        return {
            "id_token": data["id_token"],
            "refresh_token": data["refresh_token"],
            "expires_in": int(data["expires_in"]),
            "local_id": data["user_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Refresh falhou: {str(e)}")