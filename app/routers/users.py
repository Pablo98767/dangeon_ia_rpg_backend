from fastapi import APIRouter, Depends
from app.deps.auth import firebase_current_user
from app.models.user import MeOut

# ============ ADICIONE ESTE IMPORT ============
from app.services.coins_service import coins_service
# ==============================================

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=MeOut)
async def me(user = Depends(firebase_current_user)):  # ← MUDOU PARA async
    # ============ ADICIONE ESTAS LINHAS ============
    uid = user["uid"]
    user_coins = await coins_service.get_user_balance(uid)
    # ===============================================
    
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified"),
        "claims": user.get("claims") or {},
        # ============ ADICIONE ESTES CAMPOS ============
        "coin_balance": user_coins.balance,
        "total_coins_earned": user_coins.total_earned,
        "total_coins_spent": user_coins.total_spent,
        # ===============================================
    }