import httpx
from app.core.config import settings

BASE = "https://identitytoolkit.googleapis.com/v1"
SECURETOKEN = "https://securetoken.googleapis.com/v1"

async def signup_email_password(email: str, password: str) -> dict:
    url = f"{BASE}/accounts:signUp?key={settings.firebase_api_key}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    r.raise_for_status()
    return r.json()

async def signin_email_password(email: str, password: str) -> dict:
    url = f"{BASE}/accounts:signInWithPassword?key={settings.firebase_api_key}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    r.raise_for_status()
    return r.json()

async def refresh_id_token(refresh_token: str) -> dict:
    url = f"{SECURETOKEN}/token?key={settings.firebase_api_key}"
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, data=payload, headers=headers)
    r.raise_for_status()
    return r.json()
