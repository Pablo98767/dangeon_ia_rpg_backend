import stripe
from typing import Optional
from app.core.config import settings
from app.models.coins import CoinPackage

# Configurar Stripe
stripe.api_key = settings.stripe_secret_key

class StripeService:
    """Serviço para gerenciar pagamentos via Stripe"""
    
    def __init__(self):
        self.api_key = settings.stripe_secret_key
    
    def create_checkout_session(
        self,
        package: CoinPackage,
        user_id: str,
        user_email: str
    ) -> dict:
        """
        Cria uma sessão de checkout do Stripe
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'brl',
                            'unit_amount': int(package.price_brl * 100),
                            'product_data': {
                                'name': package.name,
                                'description': f'{package.coins} moedas para o seu jogo de RPG',
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=settings.stripe_success_url,
                cancel_url=settings.stripe_cancel_url,
                client_reference_id=user_id,
                customer_email=user_email,
                metadata={
                    'user_id': user_id,
                    'package_id': package.package_id,
                    'coins': package.coins,
                    'package_name': package.name,
                },
            )
            
            return {
                'session_id': session.id,
                'checkout_url': session.url,
            }
            
        except Exception as e:
            print(f"[STRIPE] Erro ao criar checkout session: {e}")
            raise Exception(f"Erro ao criar sessão de pagamento: {str(e)}")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """Verifica a assinatura do webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret
            )
            return event
        except Exception as e:
            print(f"[STRIPE WEBHOOK] Erro: {e}")
            raise Exception("Webhook inválido")
    
    def get_publishable_key(self) -> str:
        """Retorna a chave pública do Stripe"""
        return settings.stripe_publishable_key


# Instância global
stripe_service = StripeService()