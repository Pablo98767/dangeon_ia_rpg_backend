from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.deps.auth import firebase_current_user
from app.services.coins_service import coins_service
from app.services.stripe_service import stripe_service
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
    print(f"\n{'='*80}")
    print(f"[PURCHASE] 🛒 Nova solicitação de compra")
    print(f"{'='*80}")
    
    user_id = user["uid"]
    user_email = user.get("email")
    
    print(f"[PURCHASE] User ID: {user_id}")
    print(f"[PURCHASE] User Email: {user_email}")
    print(f"[PURCHASE] Package ID solicitado: {request.package_id}")
    
    # Busca o pacote
    package = coins_service.get_package_by_id(request.package_id)
    if not package:
        print(f"[PURCHASE] ❌ Pacote não encontrado: {request.package_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pacote não encontrado"
        )
    
    print(f"[PURCHASE] ✅ Pacote encontrado:")
    print(f"  - Nome: {package.name}")
    print(f"  - Moedas: {package.coins}")
    print(f"  - Preço: R$ {package.price_brl}")
    
    # ============ INTEGRAÇÃO COM STRIPE ============
    try:
        print(f"\n[PURCHASE] 💳 Criando sessão de checkout no Stripe...")
        
        # Cria sessão de checkout no Stripe
        checkout_data = stripe_service.create_checkout_session(
            package=package,
            user_id=user_id,
            user_email=user_email
        )
        
        print(f"[PURCHASE] ✅ Checkout criado com sucesso!")
        print(f"  - Session ID: {checkout_data['session_id']}")
        print(f"  - Checkout URL: {checkout_data['checkout_url'][:50]}...")
        
        # Pega saldo atual
        current_balance = (await coins_service.get_user_balance(user_id)).balance
        print(f"[PURCHASE] Saldo atual do usuário: {current_balance}")
        
        print(f"[PURCHASE] ⚠️ Moedas serão adicionadas APÓS confirmação do webhook")
        print(f"{'='*80}\n")
        
        return PurchasePackageResponse(
            transaction_id=checkout_data['session_id'],
            coins_added=0,  # Moedas serão adicionadas após confirmação do webhook
            new_balance=current_balance,
            payment_url=checkout_data['checkout_url']
        )
        
    except Exception as e:
        print(f"\n[PURCHASE] ❌ ERRO ao criar checkout:")
        print(f"  - Tipo: {type(e).__name__}")
        print(f"  - Mensagem: {str(e)}")
        import traceback
        print(f"  - Traceback: {traceback.format_exc()}")
        print(f"{'='*80}\n")
        
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
    """
    print(f"\n[ADMIN] 🔧 Adicionando moedas manualmente:")
    print(f"  - User ID: {user_id}")
    print(f"  - Amount: {amount}")
    print(f"  - Description: {description}")
    
    try:
        updated_coins = await coins_service.add_coins(
            user_id=user_id,
            amount=amount,
            transaction_type="admin_bonus",
            description=description
        )
        
        print(f"[ADMIN] ✅ Moedas adicionadas!")
        print(f"  - Novo saldo: {updated_coins.balance}\n")
        
        return {
            "message": f"{amount} moedas adicionadas com sucesso",
            "new_balance": updated_coins.balance
        }
    except Exception as e:
        print(f"[ADMIN] ❌ Erro: {e}\n")
        raise
