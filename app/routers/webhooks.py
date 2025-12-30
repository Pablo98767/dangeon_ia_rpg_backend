from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

from app.services.stripe_service import stripe_service
from app.services.coins_service import coins_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    """Webhook para receber notificações do Stripe"""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    payload = await request.body()
    
    try:
        event = stripe_service.verify_webhook_signature(payload, stripe_signature)
        
        print(f"\n{'='*60}")
        print(f"[STRIPE WEBHOOK] Evento recebido: {event['type']}")
        print(f"{'='*60}")
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            print(f"[STRIPE WEBHOOK] Sessão completada:")
            print(f"  - Session ID: {session['id']}")
            print(f"  - Payment Status: {session['payment_status']}")
            
            if session['payment_status'] == 'paid':
                user_id = session['metadata']['user_id']
                coins = int(session['metadata']['coins'])
                package_name = session['metadata']['package_name']
                
                print(f"[STRIPE WEBHOOK] Adicionando {coins} moedas para {user_id}")
                
                updated_coins = await coins_service.add_coins(
                    user_id=user_id,
                    amount=coins,
                    transaction_type="purchase",
                    description=f"Compra de {package_name}",
                    reference_id=session['id']
                )
                
                print(f"[STRIPE WEBHOOK] ✅ Novo saldo: {updated_coins.balance}")
                print(f"{'='*60}\n")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"[STRIPE WEBHOOK] ❌ Erro: {e}")
        raise HTTPException(status_code=400, detail=str(e))