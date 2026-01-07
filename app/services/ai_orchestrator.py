import os
import json
from typing import List, Dict, Optional
import httpx
from fastapi import HTTPException

SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "RPG-IA-Backend")
API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "openai/gpt-4o-mini"

# ==========================================
# SYSTEM PROMPT MELHORADO
# ==========================================
SYSTEM_PROMPT = """
Você é um motor de narrativa interativa para um jogo de aventura baseado em escolhas.

RESPONDA SEMPRE COM UM ÚNICO JSON VÁLIDO.

FORMATO OBRIGATÓRIO:

{
  "text": "texto narrativo simples",
  "choices": ["opção 1", "opção 2"],
  "state": {
    "player_hp": número inteiro,
    "room_type": "string",
    "is_game_over": true ou false
  }
}

REGRAS DE FORMATO:
- Nunca coloque JSON dentro de "text"
- Nunca serialize o objeto inteiro como string
- Se is_game_over for true, choices deve ser []
- O jogador começa com 10 de HP

REGRAS DE NARRATIVA:
1. COERÊNCIA: Continue EXATAMENTE de onde a história parou
2. CONSEQUÊNCIAS: As escolhas do jogador devem ter impacto real
3. PROGRESSÃO: A história deve avançar, não ficar em loops
4. HP: Diminua HP em situações de perigo (combate, armadilhas, quedas)
   - Perigo leve: -1 ou -2 HP
   - Perigo médio: -3 ou -4 HP
   - Perigo mortal: -5 ou mais HP
5. GAME OVER: Quando HP chegar a 0, crie um final apropriado e set is_game_over=true
6. VITÓRIA: Após 10-15 escolhas bem-sucedidas, crie um clímax e resolução
7. room_type: Use para indicar a localização atual (ex: "floresta", "caverna", "cidade", "espaço")
8. ESCOLHAS: Crie opções variadas e interessantes:
   - Ação direta vs. abordagem cautelosa
   - Combate vs. negociação
   - Risco vs. segurança
9. DESCRIÇÕES: Seja visual e envolvente, mas conciso (2-4 frases)
10. TENSÃO: Aumente gradualmente a dificuldade e stakes da história

EXEMPLOS DE BOAS ESCOLHAS:
❌ Ruim: ["Ir para esquerda", "Ir para direita"]
✅ Bom: ["Enfrentar o dragão de frente", "Procurar uma passagem secreta"]

❌ Ruim: ["Continuar", "Voltar"]
✅ Bom: ["Usar magia para congelar o inimigo", "Esquivar e contra-atacar"]
"""

# ==========================================
# PARSING
# ==========================================

def _extract_last_json_object(text: str) -> Optional[str]:
    brace_stack, in_string, escape = 0, False, False
    start_idx, last_obj = None, None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            if brace_stack == 0:
                start_idx = i
            brace_stack += 1
        elif ch == '}':
            brace_stack -= 1
            if brace_stack == 0 and start_idx is not None:
                last_obj = text[start_idx:i+1]
    return last_obj


def _parse_json_strict(content: str, current_hp: int = 10) -> Dict:
    try:
        data = json.loads(content)
    except Exception:
        blob = _extract_last_json_object(content)
        if not blob:
            raise ValueError("JSON inválido da IA")
        data = json.loads(blob)

    # Garantir campos
    state = data.get("state", {})
    player_hp = max(0, state.get("player_hp", current_hp))
    is_game_over = state.get("is_game_over", False)

    return {
        "text": data.get("text", "").strip(),
        "choices": data.get("choices", []) if not is_game_over else [],
        "state": {
            "player_hp": player_hp,
            "room_type": state.get("room_type", "desconhecido"),
            "is_game_over": is_game_over
        }
    }


# ==========================================
# IA CALL
# ==========================================

async def _chat_once(user_prompt: str, current_hp: int = 10) -> Dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME,
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 800,
            }
        )

    content = response.json()["choices"][0]["message"]["content"]
    return _parse_json_strict(content, current_hp)


# ==========================================
# MAIN
# ==========================================

async def generate_next_step(
    theme: str,
    character: str,
    history: List[dict],
    max_choices: int = 4
) -> Dict:

    # 🔥 BUSCA SEGURA DO HP
    current_hp = 10  # default
    if history:
        last_step = history[-1]
        if "state" in last_step and last_step["state"]:
            current_hp = last_step["state"].get("player_hp", 10)

    # 🔥 CONSTRUIR RESUMO DO HISTÓRICO
    history_text = ""
    if history:
        history_text = "\n=== HISTÓRIA ATÉ AGORA ===\n"
        for step in history[-5:]:  # Últimos 5 passos
            history_text += f"- {step['text']}\n"
            if step.get('chosen_choice') is not None and 'choices' in step:
                try:
                    chosen = step['choices'][step['chosen_choice']]
                    history_text += f"  → Jogador escolheu: {chosen}\n"
                except (IndexError, KeyError):
                    pass
        history_text += "=========================\n"

    user_prompt = f"""
Tema: {theme}
Personagem: {character}
HP atual: {current_hp}

{history_text}

Continue a história de forma COERENTE com o que já aconteceu.
Crie novas situações interessantes baseadas nas escolhas anteriores.
"""

    last_index = history[-1]["index"] + 1 if history else 0
    result = await _chat_once(user_prompt, current_hp)

    return {
        "index": last_index,
        "text": result["text"],
        "choices": result["choices"][:max_choices],
        "state": result["state"],
        "model": MODEL
    }