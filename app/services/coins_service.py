from datetime import datetime
from typing import Optional, List
import uuid
from google.cloud.firestore_v1 import FieldFilter
from app.models.coins import (
    CoinTransaction, 
    UserCoins, 
    CoinPackage,
    InsufficientCoinsError
)
# ============ CORREÇÃO AQUI ============
from app.services.firebase_admin_svc import firestore_client
# =======================================

# Constantes
INITIAL_BONUS_COINS = 50
STORY_CREATION_COST = 5
CHOICE_COST = 5

# Pacotes disponíveis
COIN_PACKAGES = [
    CoinPackage(
        package_id="pack_100",
        name="Pacote Iniciante",
        coins=100,
        price_brl=6.00,
        discount_percentage=None
    ),
    CoinPackage(
        package_id="pack_500",
        name="Pacote Popular",
        coins=500,
        price_brl=15.00,
        discount_percentage=16.67
    ),
    CoinPackage(
        package_id="pack_2000",
        name="Pacote Premium",
        coins=2000,
        price_brl=30.00,
        discount_percentage=50
    )
]

class CoinsService:
    def __init__(self):
        # ============ CORREÇÃO AQUI ============
        self.db = firestore_client()
        # =======================================
        self.users_coins_ref = self.db.collection("user_coins")
        self.transactions_ref = self.db.collection("coin_transactions")
    
    async def initialize_user_coins(self, user_id: str) -> UserCoins:
        """
        Inicializa moedas para um novo usuário com bônus inicial
        """
        user_coins_doc = self.users_coins_ref.document(user_id)
        
        # Verifica se já existe
        if user_coins_doc.get().exists:
            return await self.get_user_balance(user_id)
        
        # Cria registro de moedas
        user_coins = UserCoins(
            user_id=user_id,
            balance=INITIAL_BONUS_COINS,
            total_earned=INITIAL_BONUS_COINS,
            total_spent=0,
            last_transaction_at=datetime.utcnow()
        )
        
        user_coins_doc.set(user_coins.model_dump())
        
        # Registra transação de bônus inicial
        await self._create_transaction(
            user_id=user_id,
            amount=INITIAL_BONUS_COINS,
            transaction_type="initial_bonus",
            description="Bônus de boas-vindas",
            balance_after=INITIAL_BONUS_COINS
        )
        
        return user_coins
    
    async def get_user_balance(self, user_id: str) -> UserCoins:
        """
        Retorna o saldo de moedas do usuário
        """
        doc = self.users_coins_ref.document(user_id).get()
        
        if not doc.exists:
            # Se não existir, inicializa com bônus
            return await self.initialize_user_coins(user_id)
        
        return UserCoins(**doc.to_dict())
    
    async def has_sufficient_coins(self, user_id: str, required_coins: int) -> bool:
        """
        Verifica se usuário tem moedas suficientes
        """
        user_coins = await self.get_user_balance(user_id)
        return user_coins.balance >= required_coins
    
    async def deduct_coins(
        self, 
        user_id: str, 
        amount: int, 
        description: str,
        reference_id: Optional[str] = None
    ) -> UserCoins:
        """
        Deduz moedas do saldo do usuário
        """
        user_coins = await self.get_user_balance(user_id)
        
        if user_coins.balance < amount:
            raise ValueError(f"Saldo insuficiente. Você possui {user_coins.balance} moedas, mas precisa de {amount}.")
        
        # Atualiza saldo
        new_balance = user_coins.balance - amount
        user_coins.balance = new_balance
        user_coins.total_spent += amount
        user_coins.last_transaction_at = datetime.utcnow()
        user_coins.updated_at = datetime.utcnow()
        
        # Salva no Firestore
        self.users_coins_ref.document(user_id).set(user_coins.model_dump())
        
        # Registra transação
        await self._create_transaction(
            user_id=user_id,
            amount=-amount,
            transaction_type="debit",
            description=description,
            reference_id=reference_id,
            balance_after=new_balance
        )
        
        return user_coins
    
    async def add_coins(
        self, 
        user_id: str, 
        amount: int, 
        transaction_type: str,
        description: str,
        reference_id: Optional[str] = None
    ) -> UserCoins:
        """
        Adiciona moedas ao saldo do usuário
        """
        user_coins = await self.get_user_balance(user_id)
        
        # Atualiza saldo
        new_balance = user_coins.balance + amount
        user_coins.balance = new_balance
        user_coins.total_earned += amount
        user_coins.last_transaction_at = datetime.utcnow()
        user_coins.updated_at = datetime.utcnow()
        
        # Salva no Firestore
        self.users_coins_ref.document(user_id).set(user_coins.model_dump())
        
        # Registra transação
        await self._create_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
            balance_after=new_balance
        )
        
        return user_coins
    
    async def _create_transaction(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str,
        balance_after: int,
        reference_id: Optional[str] = None
    ):
        """
        Registra uma transação de moedas
        """
        transaction = CoinTransaction(
            transaction_id=str(uuid.uuid4()),
            user_id=user_id,
            amount=amount,
            balance_after=balance_after,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id
        )
        
        self.transactions_ref.document(transaction.transaction_id).set(
            transaction.model_dump()
        )
    
    async def get_user_transactions(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[CoinTransaction]:
        """
        Retorna histórico de transações do usuário
        """
        query = (
            self.transactions_ref
            .where(filter=FieldFilter("user_id", "==", user_id))
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
        )
        
        docs = query.stream()
        return [CoinTransaction(**doc.to_dict()) for doc in docs]
    
    def get_available_packages(self) -> List[CoinPackage]:
        """
        Retorna pacotes de moedas disponíveis
        """
        return [pkg for pkg in COIN_PACKAGES if pkg.is_active]
    
    def get_package_by_id(self, package_id: str) -> Optional[CoinPackage]:
        """
        Retorna um pacote específico por ID
        """
        for pkg in COIN_PACKAGES:
            if pkg.package_id == package_id:
                return pkg
        return None


# Instância global do serviço
coins_service = CoinsService()