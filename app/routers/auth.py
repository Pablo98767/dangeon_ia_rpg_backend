from fastapi import APIRouter, HTTPException
from app.models.user import RegisterIn, LoginIn, TokenOut
from app.services.firebase_identity_svc import signup_email_password, signin_email_password, refresh_id_token
from fastapi import APIRouter, Depends
from app.deps.auth import  firebase_current_user
from app.services.coins_service import coins_service
from app.services import firebase_identity_svc


router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/verify")
def verify(user = Depends(firebase_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
        "aud": user.get("aud"),
        "iss": user.get("iss"),
    }
@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn):
    try:
        data = await signup_email_password(body.email, body.password)
        return {
            "id_token": data["idToken"],
            "refresh_token": data["refreshToken"],
            "expires_in": int(data["expiresIn"]),
            "local_id": data["localId"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registro falhou: {e}")

@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn):
    try:
        data = await signin_email_password(body.email, body.password)
        return {
            "id_token": data["idToken"],
            "refresh_token": data["refreshToken"],
            "expires_in": int(data["expiresIn"]),
            "local_id": data["localId"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login falhou: {e}")

@router.post("/refresh", response_model=TokenOut)
async def refresh(refresh_token: str):
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
        raise HTTPException(status_code=400, detail=f"Refresh falhou: {e}")
    


@router.post("/register", response_model=TokenOut)
async def register(user_data: RegisterIn):
    """Register a new user"""
    try:
        result = await firebase_identity_svc.register_user(
            email=user_data.email,
            password=user_data.password
        )
        
        # ADICIONE ESTAS LINHAS - Inicializa moedas para novo usuário
        await coins_service.initialize_user_coins(result.local_id)
        
        return {
            "id_token": result.id_token,
            "refresh_token": result.refresh_token,
            "expires_in": result.expires_in,
            "local_id": result.local_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
