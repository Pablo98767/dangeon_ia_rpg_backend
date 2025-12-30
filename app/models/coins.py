from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class CoinTransaction(BaseModel):
    """Modelo para transações de moedas"""
    transaction_id: str
    user_id: str
    amount: int  # positivo = crédito, negativo = débito
    balance_after: int
    transaction_type: Literal["purchase", "debit", "initial_bonus", "refund"]
    description: str
    reference_id: Optional[str] = None  # story_id ou payment_id
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CoinPackage(BaseModel):
    """Pacotes de moedas disponíveis"""
    package_id: str
    name: str
    coins: int
    price_brl: float
    discount_percentage: Optional[float] = None
    is_active: bool = True

class UserCoins(BaseModel):
    """Saldo de moedas do usuário"""
    user_id: str
    balance: int
    total_earned: int = 0
    total_spent: int = 0
    last_transaction_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Schemas para requisições/respostas
class CoinBalanceResponse(BaseModel):
    balance: int
    total_earned: int
    total_spent: int

class PurchasePackageRequest(BaseModel):
    package_id: str
    payment_method: Literal["pix", "credit_card", "stripe"]  # Stripe virá depois

class PurchasePackageResponse(BaseModel):
    transaction_id: str
    coins_added: int
    new_balance: int
    payment_url: Optional[str] = None  # Para PIX ou Stripe checkout
    
class InsufficientCoinsError(BaseModel):
    detail: str
    current_balance: int
    required_coins: int
    packages_available: list[CoinPackage]