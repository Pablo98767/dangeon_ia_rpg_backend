from fastapi import APIRouter, Depends
from app.deps.auth import firebase_current_user
from app.models.user import MeOut

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=MeOut)
def me(user = Depends(firebase_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified"),
        "claims": user.get("claims") or {},
    }
