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

from app.services.firebase_admin_svc import firestore_client


# =======================
# Constantes
# =======================
INITIAL_BONUS_COINS = 50
STORY_CREATION_COST = 5
CHOICE_COST = 5


# =======================
# Pacotes disponíveis
# =======================
COIN_PACKAGES = [
    CoinPackage(
        package_id="pack_100",
        name="Pacote Iniciante",
        coins=100,
        price_brl=1.00,
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
        self.db = firestore_client()
        self.users_coins_ref = self.db.collection("user_coins")
        self.transactions_ref = self.db.collection("coin_transactions")

    # =========================================================
    # Inicialização segura (idempotente)
    # =========================================================
    async def initialize_user_coins(self, user_id: str) -> UserCoins:
        user_doc_ref = self.users_coins_ref.document(user_id)
        doc = user_doc_ref.get()

        if doc.exists:
            return UserCoins(**doc.to_dict())

        user_coins = UserCoins(
            user_id=user_id,
            balance=INITIAL_BONUS_COINS,
            total_earned=INITIAL_BONUS_COINS,
            total_spent=0,
            last_transaction_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        user_doc_ref.set(
            user_coins.model_dump(),
            merge=True
        )

        await self._create_transaction(
            user_id=user_id,
            amount=INITIAL_BONUS_COINS,
            transaction_type="initial_bonus",
            description="Bônus de boas-vindas",
            balance_after=INITIAL_BONUS_COINS
        )

        return user_coins

    # =========================================================
    # Saldo
    # =========================================================
    async def get_user_balance(self, user_id: str) -> UserCoins:
        doc = self.users_coins_ref.document(user_id).get()

        if not doc.exists:
            return await self.initialize_user_coins(user_id)

        return UserCoins(**doc.to_dict())

    async def has_sufficient_coins(self, user_id: str, required_coins: int) -> bool:
        user_coins = await self.get_user_balance(user_id)
        return user_coins.balance >= required_coins

    # =========================================================
    # Débito
    # =========================================================
    async def deduct_coins(
        self,
        user_id: str,
        amount: int,
        description: str,
        reference_id: Optional[str] = None
    ) -> UserCoins:

        user_coins = await self.get_user_balance(user_id)

        if user_coins.balance < amount:
            raise InsufficientCoinsError(
                f"Saldo insuficiente. Possui {user_coins.balance}, precisa de {amount}."
            )

        new_balance = user_coins.balance - amount

        user_coins.balance = new_balance
        user_coins.total_spent += amount
        user_coins.last_transaction_at = datetime.utcnow()
        user_coins.updated_at = datetime.utcnow()

        self.users_coins_ref.document(user_id).set(
            user_coins.model_dump(),
            merge=True
        )

        await self._create_transaction(
            user_id=user_id,
            amount=-amount,
            transaction_type="debit",
            description=description,
            reference_id=reference_id,
            balance_after=new_balance
        )

        return user_coins

    # =========================================================
    # Crédito (COMPRA) - 🔥 CORRIGIDO
    # =========================================================
    async def add_coins(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str,
        reference_id: Optional[str] = None
    ) -> UserCoins:
        
        print(f"\n[COINS_SERVICE] Iniciando add_coins:")
        print(f"  - user_id: {user_id}")
        print(f"  - amount: {amount}")
        print(f"  - reference_id: {reference_id}")

        # 🔒 Proteção contra duplicidade (webhook / retry)
        if reference_id:
            existing_docs = list(
                self.transactions_ref
                .where(filter=FieldFilter("reference_id", "==", reference_id))
                .limit(1)
                .stream()
            )
            
            if existing_docs:
                print(f"[COINS_SERVICE] ⚠️ Transação duplicada detectada! reference_id: {reference_id}")
                # 🔥 FIX: Retorna o saldo ATUAL do usuário, não o antigo
                user_coins_updated = await self.get_user_balance(user_id)
                print(f"[COINS_SERVICE] Saldo atual do usuário: {user_coins_updated.balance}")
                return user_coins_updated

        # Busca saldo atual
        user_coins = await self.get_user_balance(user_id)
        print(f"[COINS_SERVICE] Saldo ANTES: {user_coins.balance}")

        new_balance = user_coins.balance + amount

        user_coins.balance = new_balance
        user_coins.total_earned += amount
        user_coins.last_transaction_at = datetime.utcnow()
        user_coins.updated_at = datetime.utcnow()

        # 🔥 Salvando no Firestore com try/catch
        try:
            self.users_coins_ref.document(user_id).set(
                user_coins.model_dump(),
                merge=True
            )
            print(f"[COINS_SERVICE] ✅ Firestore atualizado! Novo saldo: {new_balance}")
        except Exception as e:
            print(f"[COINS_SERVICE] ❌ ERRO ao salvar no Firestore: {e}")
            raise

        # Cria transação
        try:
            await self._create_transaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                reference_id=reference_id,
                balance_after=new_balance
            )
            print(f"[COINS_SERVICE] ✅ Transação criada com sucesso")
        except Exception as e:
            print(f"[COINS_SERVICE] ❌ ERRO ao criar transação: {e}")
            raise

        return user_coins

    # =========================================================
    # Transações
    # =========================================================
    async def _create_transaction(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str,
        balance_after: int,
        reference_id: Optional[str] = None
    ):
        transaction = CoinTransaction(
            transaction_id=str(uuid.uuid4()),
            user_id=user_id,
            amount=amount,
            balance_after=balance_after,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
            created_at=datetime.utcnow()
        )

        self.transactions_ref.document(transaction.transaction_id).set(
            transaction.model_dump(),
            merge=True
        )

    async def get_user_transactions(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[CoinTransaction]:

        query = (
            self.transactions_ref
            .where(filter=FieldFilter("user_id", "==", user_id))
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
        )

        docs = query.stream()
        return [CoinTransaction(**doc.to_dict()) for doc in docs]

    # =========================================================
    # Pacotes
    # =========================================================
    def get_available_packages(self) -> List[CoinPackage]:
        return [pkg for pkg in COIN_PACKAGES if pkg.is_active]

    def get_package_by_id(self, package_id: str) -> Optional[CoinPackage]:
        for pkg in COIN_PACKAGES:
            if pkg.package_id == package_id:
                return pkg
        return None


# Instância global
coins_service = CoinsService()
