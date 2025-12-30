import os
import json
from typing import List, Dict, Optional
import httpx
from fastapi import HTTPException

# ==========================================
# CONFIGURAÇÕES - GPT-4o-mini via OpenRouter
# ==========================================
SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "RPG-IA-Backend")
API_KEY = os.getenv("OPENROUTER_API_KEY")

# 🚀 MODELO ATUALIZADO: GPT-4o-mini (muito mais poderoso!)
MODEL = "openai/gpt-4o-mini"

# ==========================================
# SYSTEM PROMPT OTIMIZADO
# ==========================================
SYSTEM_PROMPT = """
Você é um narrador de histórias interativas de RPG extremamente criativo e envolvente.
Responda SEMPRE em JSON estrito, no formato:
{
  "text": "trecho da história em português",
  "choices": ["opção 1", "opção 2", "opção 3", "opção 4"]
}

REGRAS IMPORTANTES:
- "text": Deve conter uma narrativa envolvente, descritiva e imersiva (200-400 palavras)
- "choices": Deve ter entre 2 e 4 opções curtas, claras e mutuamente exclusivas
- Nunca inclua comentários fora do JSON. Nunca use markdown. Apenas JSON puro.
- Mantenha a coerência da história, personagens consistentes e lógica interna impecável
- Crie histórias com início, desenvolvimento e conclusões épicas
- Use elementos dramáticos, reviravoltas e momentos emocionantes
- Adapte-se ao tom e tema escolhido pelo jogador

IMPORTANTE: Responda APENAS com o objeto JSON, sem nenhum texto adicional antes ou depois.
"""

# ==========================================
# FUNÇÕES AUXILIARES DE PARSING JSON
# ==========================================

def _extract_last_json_object(text: str) -> Optional[str]:
    """
    Extrai o último objeto JSON válido de uma string,
    mesmo que contenha texto antes ou depois.
    """
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
    """
    Tenta fazer o parse do JSON de forma inteligente.
    Primeiro tenta parse direto, depois procura por objeto JSON,
    e por último retorna fallback com escolhas padrão.
    """
    # Tentativa 1: Parse direto
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "text" in data and isinstance(data.get("choices"), list):
            return data
    except Exception:
        pass

    # Tentativa 2: Extrair último objeto JSON válido
    blob = _extract_last_json_object(content)
    if blob:
        try:
            data = json.loads(blob)
            if isinstance(data, dict) and "text" in data and isinstance(data.get("choices"), list):
                return data
        except Exception:
            pass

    # Fallback: Retorna o texto completo com escolhas padrão
    return {
        "text": content.strip(),
        "choices": ["Seguir adiante", "Recuar com cautela", "Investigar ao redor"]
    }


# ==========================================
# FUNÇÃO DE CHAMADA À IA (GPT-4o-mini)
# ==========================================

async def _chat_once(user_prompt: str) -> Dict:
    """
    Faz uma chamada única à API da OpenRouter usando GPT-4o-mini.
    Retorna um dicionário com 'text' e 'choices'.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
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
                    ],
                    "temperature": 0.8,  # Criatividade balanceada
                    "max_tokens": 800,   # Permite respostas mais elaboradas
                }
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Timeout ao chamar a IA")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Erro de conexão com a IA: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=503, 
            detail=f"Erro ao chamar IA: {response.status_code} - {response.text}"
        )

    # Parse da resposta
    response_data = response.json()
    content = response_data["choices"][0]["message"]["content"]
    
    # Parse inteligente do JSON
    data = _parse_json_strict(content)
    
    # Validação e normalização das escolhas
    choices = data.get("choices") or []
    if len(choices) < 2:
        choices = ["Seguir adiante", "Recuar com cautela", "Investigar ao redor"]
    elif len(choices) > 4:
        choices = choices[:4]
    
    return {
        "text": (data.get("text") or "").strip(),
        "choices": choices
    }


# ==========================================
# FUNÇÃO PRINCIPAL DE GERAÇÃO DE HISTÓRIA
# ==========================================

async def generate_next_step(
    theme: str, 
    character: str, 
    history: List[dict], 
    max_choices: int = 4
) -> Dict:
    """
    Gera o próximo passo da história baseado no tema, personagem e histórico.
    
    Args:
        theme: Tema/gênero da história (fantasia, sci-fi, terror, etc)
        character: Descrição do personagem principal
        history: Lista de eventos anteriores da história
        max_choices: Número máximo de escolhas (2-4)
    
    Returns:
        Dict com: index, text, choices, model
    """
    
    # Construir resumo do histórico (últimas 3 interações)
    recap = ""
    if history:
        recap = "📜 RESUMO DOS EVENTOS RECENTES:\n"
        for h in history[-3:]:
            chosen_idx = h.get("chosen_index")
            tag = "" if chosen_idx is None else f" [Escolha: {chosen_idx + 1}]"
            recap += f"• {h['text'][:250]}{tag}\n"
    
    # Construir prompt para a IA
    user_prompt = f"""
🎮 GERAÇÃO DE HISTÓRIA INTERATIVA

📖 TEMA: {theme}
👤 PERSONAGEM: {character}

{recap}

🎯 TAREFA:
Gere o próximo trecho emocionante da história com no máximo {max_choices} escolhas de ação.

LEMBRE-SE:
- Crie uma narrativa envolvente e imersiva
- As escolhas devem ser interessantes e impactantes
- Mantenha a coerência com os eventos anteriores
- Responda APENAS com JSON no formato especificado
"""

    # Calcular o índice do próximo passo
    last_index = history[-1]["index"] + 1 if history else 0

    try:
        # Chamada à IA
        result = await _chat_once(user_prompt)
        
        # Normalizar número de escolhas
        result["choices"] = (result["choices"] or [])[:max(2, min(4, max_choices))]
        
        # Retornar resposta estruturada
        return {
            "index": last_index,
            "text": result["text"],
            "choices": result["choices"],
            "model": MODEL,
        }
        
    except HTTPException:
        raise  # Re-lança HTTPExceptions
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Serviço de IA indisponível: {type(e).__name__} - {str(e)}"
        )


# ==========================================
# INFORMAÇÕES DO MODELO (para logging/debug)
# ==========================================

def get_model_info() -> Dict:
    """
    Retorna informações sobre o modelo atual.
    """
    return {
        "model": MODEL,
        "provider": "OpenRouter",
        "base_model": "OpenAI GPT-4o-mini",
        "context_window": "128k tokens",
        "pricing": {
            "input": "$0.15 per 1M tokens",
            "output": "$0.60 per 1M tokens"
        }
    }