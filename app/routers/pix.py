from fastapi import APIRouter
from app.services.pix_service import PixService

router = APIRouter(prefix="/pix", tags=["PIX"])

pix_service = PixService()

@router.get("/")
def get_pix_key():
    return {
        "pix_key": pix_service.get_pix_key()
    }

@router.get("/payload")
def get_pix_payload():
    return {
        "payload": pix_service.generate_static_payload()
    }
