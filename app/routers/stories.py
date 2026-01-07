from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List
from fastapi.responses import JSONResponse

from app.deps.auth import firebase_current_user
from app.models.story import StartStoryIn, StepOut, ChooseIn, StoryMetaOut, StorySummaryOut
from app.services.story_service import StoryService
from app.services.ai_orchestrator import generate_next_step
from app.services.coins_service import coins_service, STORY_CREATION_COST, CHOICE_COST

S = StoryService()
router = APIRouter(prefix="/stories", tags=["stories"])

def _ensure_owner(story_id: str, uid: str):
    story = S.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="História não encontrada")
    if story["owner_uid"] != uid:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return story

@router.post("", response_model=StepOut, status_code=201)
async def start_story(body: StartStoryIn, user=Depends(firebase_current_user)):
    uid = user["uid"]
    
    has_coins = await coins_service.has_sufficient_coins(uid, STORY_CREATION_COST)
    if not has_coins:
        user_coins = await coins_service.get_user_balance(uid)
        raise HTTPException(
            status_code=402,
            detail=f"Moedas insuficientes. Você tem {user_coins.balance} moedas, mas precisa de {STORY_CREATION_COST}."
        )
    
    story_id = S.new_story(uid, body.theme_prompt, body.character_prompt)
    
    try:
        await coins_service.deduct_coins(
            user_id=uid,
            amount=STORY_CREATION_COST,
            description="Criação de nova história",
            reference_id=story_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar moedas: {str(e)}")

    step_payload = await generate_next_step(
        theme=body.theme_prompt,
        character=body.character_prompt,
        history=[],
        max_choices=body.initial_choices
    )

    step_id = S.add_step(
        story_id, 
        step_payload["index"], 
        step_payload["text"], 
        step_payload["choices"],
        step_payload.get("state")  # 🔥 PASSANDO STATE
    )

    return StepOut(
        story_id=story_id,
        step_id=step_id,
        index=step_payload["index"],
        text=step_payload["text"],
        choices=step_payload["choices"],
        created_at=datetime.utcnow(),
        state=step_payload.get("state")
    )

@router.post("/{story_id}/choose", response_model=StepOut)
async def choose_and_continue(story_id: str, body: ChooseIn, user=Depends(firebase_current_user)):
    uid = user["uid"]
    story = _ensure_owner(story_id, uid)
    current_step_id = story.get("current_step_id")
    if not current_step_id:
        raise HTTPException(status_code=400, detail="História sem passo atual")

    step = S.get_step(story_id, current_step_id)
    if not step:
        raise HTTPException(status_code=500, detail="Passo atual não encontrado")
    if body.choice_index < 0 or body.choice_index >= len(step["choices"]):
        raise HTTPException(status_code=400, detail="Índice de escolha inválido")

    has_coins = await coins_service.has_sufficient_coins(uid, CHOICE_COST)
    if not has_coins:
        user_coins = await coins_service.get_user_balance(uid)
        raise HTTPException(
            status_code=402,
            detail=f"Moedas insuficientes. Você tem {user_coins.balance} moedas, mas precisa de {CHOICE_COST}."
        )
    
    try:
        await coins_service.deduct_coins(
            user_id=uid,
            amount=CHOICE_COST,
            description=f"Escolha na história: {step['choices'][body.choice_index]}",
            reference_id=story_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar moedas: {str(e)}")

    S.choose(story_id, current_step_id, body.choice_index)

    hist = S.recent_history(story_id, k=10)
    hist = sorted(hist, key=lambda d: d["index"])
    max_choices = min(4, 2 + len(hist) // 2)

    next_payload = await generate_next_step(
        theme=story["theme_prompt"],
        character=story["character_prompt"],
        history=hist,
        max_choices=max_choices
    )

    next_step_id = S.add_step(
        story_id, 
        next_payload["index"], 
        next_payload["text"], 
        next_payload["choices"],
        next_payload.get("state")  # 🔥 PASSANDO STATE
    )

    return StepOut(
        story_id=story_id,
        step_id=next_step_id,
        index=next_payload["index"],
        text=next_payload["text"],
        choices=next_payload["choices"],
        created_at=datetime.utcnow(),
        state=next_payload.get("state")
    )

@router.post("/{story_id}/steps/send", response_model=StepOut)
async def send_steps(story_id: str, user=Depends(firebase_current_user)):
    uid = user["uid"]
    story = _ensure_owner(story_id, uid)

    has_coins = await coins_service.has_sufficient_coins(uid, CHOICE_COST)
    if not has_coins:
        user_coins = await coins_service.get_user_balance(uid)
        raise HTTPException(
            status_code=402,
            detail=f"Moedas insuficientes. Você tem {user_coins.balance} moedas, mas precisa de {CHOICE_COST}."
        )
    
    try:
        await coins_service.deduct_coins(
            user_id=uid,
            amount=CHOICE_COST,
            description="Envio de passos da história",
            reference_id=story_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar moedas: {str(e)}")

    steps = S.list_steps(story_id)
    steps = sorted(steps, key=lambda d: d["index"])
    max_choices = min(4, 2 + len(steps) // 2)

    next_payload = await generate_next_step(
        theme=story["theme_prompt"],
        character=story["character_prompt"],
        history=steps,
        max_choices=max_choices
    )

    step_id = S.add_step(
        story_id, 
        next_payload["index"], 
        next_payload["text"], 
        next_payload["choices"],
        next_payload.get("state")  # 🔥 PASSANDO STATE
    )

    return StepOut(
        story_id=story_id,
        step_id=step_id,
        index=next_payload["index"],
        text=next_payload["text"],
        choices=next_payload["choices"],
        created_at=datetime.utcnow(),
        state=next_payload.get("state")
    )

@router.post("/{story_id}/continue", response_model=StepOut)
async def continue_story(story_id: str, user=Depends(firebase_current_user)):
    uid = user["uid"]
    story = _ensure_owner(story_id, uid)

    has_coins = await coins_service.has_sufficient_coins(uid, CHOICE_COST)
    if not has_coins:
        user_coins = await coins_service.get_user_balance(uid)
        raise HTTPException(
            status_code=402,
            detail=f"Moedas insuficientes. Você tem {user_coins.balance} moedas, mas precisa de {CHOICE_COST}."
        )
    
    try:
        await coins_service.deduct_coins(
            user_id=uid,
            amount=CHOICE_COST,
            description="Continuação da história",
            reference_id=story_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar moedas: {str(e)}")

    hist = S.recent_history(story_id, k=10)
    hist = sorted(hist, key=lambda d: d["index"])
    max_choices = min(4, 2 + len(hist) // 2)

    next_payload = await generate_next_step(
        theme=story["theme_prompt"],
        character=story["character_prompt"],
        history=hist,
        max_choices=max_choices
    )

    next_step_id = S.add_step(
        story_id,
        next_payload["index"],
        next_payload["text"],
        next_payload["choices"],
        next_payload.get("state")  # 🔥 PASSANDO STATE
    )

    return StepOut(
        story_id=story_id,
        step_id=next_step_id,
        index=next_payload["index"],
        text=next_payload["text"],
        choices=next_payload["choices"],
        created_at=datetime.utcnow(),
        state=next_payload.get("state")
    )

@router.get("/{story_id}", response_model=StoryMetaOut)
def get_story_meta(story_id: str, user=Depends(firebase_current_user)):
    uid = user["uid"]
    story = _ensure_owner(story_id, uid)
    return {
        "story_id": story_id,
        "owner_uid": story["owner_uid"],
        "theme_prompt": story["theme_prompt"],
        "character_prompt": story["character_prompt"],
        "created_at": story["created_at"],
        "updated_at": story["updated_at"],
        "status": story["status"],
        "current_step_id": story.get("current_step_id"),
    }

@router.get("/{story_id}/steps", response_model=List[StepOut])
def list_steps(story_id: str, user=Depends(firebase_current_user)):
    uid = user["uid"]
    _ensure_owner(story_id, uid)
    return S.list_steps(story_id)

@router.get("", response_model=List[StorySummaryOut])
def list_my_stories(user=Depends(firebase_current_user)):
    uid = user["uid"]
    docs = S.list_user_stories(uid, limit=50)
    out = []
    for d in docs:
        last_text = None
        if d.get("current_step_id"):
            step = S.get_step(d["story_id"], d["current_step_id"])
            last_text = step["text"] if step else None
        out.append({
            "story_id": d["story_id"],
            "created_at": d["created_at"],
            "updated_at": d["updated_at"],
            "status": d["status"],
            "last_text": last_text
        })
    return out