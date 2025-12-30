from fastapi import Depends, HTTPException, status
from app.deps.auth import get_current_user
from app.services.coins_service import coins_service, STORY_CREATION_COST, CHOICE_COST
from app.models.coins import InsufficientCoinsError

async def check_coins_for_story_creation(
    current_user: dict = Depends(get_current_user)
):
    """
    Dependency para verificar se usuário tem moedas para criar história
    """
    user_id = current_user["uid"]
    
    has_coins = await coins_service.has_sufficient_coins(user_id, STORY_CREATION_COST)
    
    if not has_coins:
        user_coins = await coins_service.get_user_balance(user_id)
        packages = coins_service.get_available_packages()
        
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Moedas insuficientes para criar uma nova história",
                "current_balance": user_coins.balance,
                "required_coins": STORY_CREATION_COST,
                "packages_available": [pkg.model_dump() for pkg in packages]
            }
        )
    
    return current_user

async def check_coins_for_choice(
    current_user: dict = Depends(get_current_user)
):
    """
    Dependency para verificar se usuário tem moedas para fazer uma escolha
    """
    user_id = current_user["uid"]
    
    has_coins = await coins_service.has_sufficient_coins(user_id, CHOICE_COST)
    
    if not has_coins:
        user_coins = await coins_service.get_user_balance(user_id)
        packages = coins_service.get_available_packages()
        
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Moedas insuficientes para continuar a história. Compre um pacote de moedas para continuar jogando!",
                "current_balance": user_coins.balance,
                "required_coins": CHOICE_COST,
                "packages_available": [pkg.model_dump() for pkg in packages]
            }
        )
    
    return current_user