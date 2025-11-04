from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    id_token: str
    refresh_token: str
    expires_in: int
    local_id: str

class MeOut(BaseModel):
    uid: str
    email: EmailStr | None = None
    email_verified: bool | None = None
    claims: dict | None = None
