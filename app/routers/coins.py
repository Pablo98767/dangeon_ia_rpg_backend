from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.deps.auth import firebase_current_user
from app.services.coins_service import coins_service
from app.services.stripe_service import stripe_service  # ← IMPORTANTE
from app.models.coins import (
    CoinBalanceResponse,
    CoinTransaction,
    CoinPackage,
    PurchasePackageRequest,
    PurchasePackageResponse
)

router = APIRouter(prefix="/coins", tags=["coins"])

@router.get("/balance", response_model=CoinBalanceResponse)
async def get_coin_balance(
    user = Depends(firebase_current_user)
):
    """
    Retorna o saldo atual de moedas do usuário
    """
    user_id = user["uid"]
    user_coins = await coins_service.get_user_balance(user_id)
    
    return CoinBalanceResponse(
        balance=user_coins.balance,
        total_earned=user_coins.total_earned,
        total_spent=user_coins.total_spent
    )

@router.get("/transactions", response_model=List[CoinTransaction])
async def get_transactions_history(
    limit: int = 50,
    user = Depends(firebase_current_user)
):
    """
    Retorna o histórico de transações de moedas
    """
    user_id = user["uid"]
    transactions = await coins_service.get_user_transactions(user_id, limit)
    return transactions

@router.get("/packages", response_model=List[CoinPackage])
async def get_coin_packages():
    """
    Lista todos os pacotes de moedas disponíveis para compra
    """
    return coins_service.get_available_packages()

@router.post("/purchase", response_model=PurchasePackageResponse, status_code=status.HTTP_201_CREATED)
async def purchase_coin_package(
    request: PurchasePackageRequest,
    user = Depends(firebase_current_user)
):
    """
    Inicia o processo de compra de um pacote de moedas via Stripe
    """
    user_id = user["uid"]
    user_email = user.get("email")
    
    # Busca o pacote
    package = coins_service.get_package_by_id(request.package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pacote não encontrado"
        )
    
    # ============ INTEGRAÇÃO COM STRIPE (CÓDIGO ATUALIZADO) ============
    try:
        # Cria sessão de checkout no Stripe
        checkout_data = stripe_service.create_checkout_session(
            package=package,
            user_id=user_id,
            user_email=user_email
        )
        
        return PurchasePackageResponse(
            transaction_id=checkout_data['session_id'],
            coins_added=0,  # Moedas serão adicionadas após confirmação do webhook
            new_balance=(await coins_service.get_user_balance(user_id)).balance,
            payment_url=checkout_data['checkout_url']
        )
        
    except Exception as e:
        print(f"[STRIPE] Erro ao criar checkout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar sessão de pagamento: {str(e)}"
        )

@router.get("/stripe/config")
async def get_stripe_config():
    """
    Retorna a chave pública do Stripe para o frontend
    """
    return {
        "publishable_key": stripe_service.get_publishable_key()
    }

@router.post("/admin/add-coins/{user_id}", include_in_schema=False)
async def admin_add_coins(
    user_id: str,
    amount: int,
    description: str = "Moedas adicionadas pelo admin",
    user = Depends(firebase_current_user)
):
    """
    Endpoint administrativo para adicionar moedas manualmente
    (útil para testes ou bônus promocionais)
    """
    # TODO: Adicionar verificação de admin role
    
    updated_coins = await coins_service.add_coins(
        user_id=user_id,
        amount=amount,
        transaction_type="purchase",
        description=description
    )
    
    return {
        "message": f"{amount} moedas adicionadas com sucesso",
        "new_balance": updated_coins.balance
    }