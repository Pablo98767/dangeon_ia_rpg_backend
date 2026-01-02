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
    
    print(f"\n{'='*80}")
    print(f"[WEBHOOK] 🔔 Requisição recebida do Stripe")
    print(f"{'='*80}")
    
    if not stripe_signature:
        print("[WEBHOOK] ❌ Assinatura do Stripe ausente!")
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    payload = await request.body()
    
    try:
        # Verifica assinatura
        event = stripe_service.verify_webhook_signature(payload, stripe_signature)
        
        print(f"[WEBHOOK] ✅ Assinatura verificada")
        print(f"[WEBHOOK] Tipo do evento: {event['type']}")
        print(f"[WEBHOOK] Event ID: {event.get('id', 'N/A')}")
        
        # Processa apenas checkout completado
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            print(f"\n[WEBHOOK] 💳 Checkout Session Completed:")
            print(f"  - Session ID: {session['id']}")
            print(f"  - Payment Status: {session.get('payment_status', 'N/A')}")
            print(f"  - Amount Total: {session.get('amount_total', 0) / 100} BRL")
            
            # Só processa se pagamento foi confirmado
            if session.get('payment_status') == 'paid':
                
                # Extrai metadados
                try:
                    metadata = session.get('metadata', {})
                    user_id = metadata.get('user_id')
                    coins = metadata.get('coins')
                    package_name = metadata.get('package_name', 'Pacote')
                    
                    print(f"\n[WEBHOOK] 📦 Metadata extraída:")
                    print(f"  - user_id: {user_id}")
                    print(f"  - coins: {coins}")
                    print(f"  - package_name: {package_name}")
                    
                    # Validações
                    if not user_id:
                        raise ValueError("user_id não encontrado no metadata")
                    if not coins:
                        raise ValueError("coins não encontrado no metadata")
                    
                    coins_int = int(coins)
                    
                    print(f"\n[WEBHOOK] 🪙 Processando adição de moedas...")
                    
                    # Adiciona as moedas
                    updated_coins = await coins_service.add_coins(
                        user_id=user_id,
                        amount=coins_int,
                        transaction_type="purchase",
                        description=f"Compra de {package_name}",
                        reference_id=session['id']  # Usa session ID como reference
                    )
                    
                    print(f"\n[WEBHOOK] ✅ SUCESSO!")
                    print(f"  - Usuário: {user_id}")
                    print(f"  - Moedas adicionadas: {coins_int}")
                    print(f"  - Novo saldo: {updated_coins.balance}")
                    print(f"  - Total ganho: {updated_coins.total_earned}")
                    print(f"{'='*80}\n")
                    
                except Exception as e:
                    print(f"\n[WEBHOOK] ❌ ERRO ao processar pagamento:")
                    print(f"  - Erro: {str(e)}")
                    print(f"  - Session ID: {session.get('id', 'N/A')}")
                    print(f"  - Metadata: {session.get('metadata', {})}")
                    print(f"{'='*80}\n")
                    raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")
            
            else:
                print(f"[WEBHOOK] ⚠️ Pagamento não confirmado. Status: {session.get('payment_status')}")
        
        else:
            print(f"[WEBHOOK] ℹ️ Evento ignorado: {event['type']}")
        
        return {"status": "success", "event_type": event['type']}
        
    except ValueError as e:
        print(f"[WEBHOOK] ❌ Erro de validação: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        print(f"[WEBHOOK] ❌ Erro inesperado: {e}")
        print(f"  - Tipo: {type(e).__name__}")
        import traceback
        print(f"  - Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))
