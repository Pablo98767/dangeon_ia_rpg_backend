import os
import json
from typing import List, Dict, Optional
import requests
from fastapi import HTTPException

SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "RPG-IA-Backend")
API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """
Você é um narrador de histórias interativas.
Responda SEMPRE em JSON estrito, no formato:
{
  "text": "trecho da história em português",
  "choices": ["opção 1", "opção 2", "..."]
}
- "choices" deve ter entre 2 e 4 opções curtas, claras, mutuamente exclusivas.
- Nunca inclua comentários fora do JSON. Nunca use markdown. Apenas JSON.
- Nunca fuja da coerência da história em cada escolha. Mantenha a lógica interna e os personagens consistentes.
- Sempre faça início da história, meio e fim... para que a história seja iniciada e tenha sempre um final.
"""

MODEL = "mistralai/mistral-7b-instruct:free"

def _extract_last_json_object(text: str) -> Optional[str]:
    brace_stack = 0
    in_string = False
    escape = False
    start_idx = None
    last_obj = None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == '{':
                if brace_stack == 0:
                    start_idx = i
                brace_stack += 1
            elif ch == '}':
                if brace_stack > 0:
                    brace_stack -= 1
                    if brace_stack == 0 and start_idx is not None:
                        last_obj = text[start_idx:i+1]
                        start_idx = None
    return last_obj

def _parse_json_strict(content: str) -> Dict:
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "text" in data and isinstance(data.get("choices"), list):
            return data
    except Exception:
        pass

    blob = _extract_last_json_object(content)
    if blob:
        try:
            data = json.loads(blob)
            if isinstance(data, dict) and "text" in data and isinstance(data.get("choices"), list):
                return data
        except Exception:
            pass

    return {
        "text": content.strip(),
        "choices": ["Seguir adiante", "Recuar com cautela"]
    }

import httpx

async def _chat_once(user_prompt: str) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME,
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            }
        )

    if response.status_code != 200:
        raise HTTPException(status_code=503, detail=f"Erro ao chamar IA: {response.status_code} {response.text}")

    content = response.json()["choices"][0]["message"]["content"]
    data = _parse_json_strict(content)
    choices = data.get("choices") or []
    if len(choices) < 2:
        choices = ["Seguir adiante", "Recuar com cautela"]
    elif len(choices) > 4:
        choices = choices[:4]
    return {"text": (data.get("text") or "").strip(), "choices": choices}


async def generate_next_step(theme: str, character: str, history: List[dict], max_choices: int = 4) -> Dict:
    recap = ""
    if history:
        recap = "Resumo breve dos últimos eventos:\n"
        for h in history[-3:]:
            tag = "" if h.get("chosen_index") is None else f" [Escolha:{h['chosen_index']}]"
            recap += f"- {h['text'][:200]}{tag}\n"

    user_prompt = (
        f"Tema: {theme}\n"
        f"Personagem: {character}\n"
        f"{recap}\n"
        f"Gere o próximo trecho da história com no máximo {max_choices} escolhas.\n"
        f"Lembre: responda APENAS JSON no formato especificado."
    )

    last_index = history[-1]["index"] + 1 if history else 0

    try:
        result = await _chat_once(user_prompt)  # ✅ Aqui é onde você altera
        result["choices"] = (result["choices"] or [])[:max(2, min(4, max_choices))]
        return {
            "index": last_index,
            "text": result["text"],
            "choices": result["choices"],
            "model": MODEL,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serviço de IA indisponível ({type(e).__name__})")


