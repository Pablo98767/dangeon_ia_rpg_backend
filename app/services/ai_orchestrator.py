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

MODEL = "openai/gpt-4o-mini"

# ==========================================
# SYSTEM PROMPT OTIMIZADO V2
# ==========================================
SYSTEM_PROMPT = """
Você é um NARRADOR DE RPG INTERATIVO, responsável por conduzir uma história dinâmica, coerente e consequente.
Você NÃO é apenas um escritor.
Você é um GERENCIADOR DE ESTADO DE JOGO.
Responda SEMPRE e EXCLUSIVAMENTE em JSON válido.
NUNCA escreva texto fora do JSON.
NUNCA use markdown.
NUNCA explique regras ao jogador.

========================
ESTRUTURA OBRIGATÓRIA
========================
{
  "scene": {
    "type": "narrative | combat | decision | consequence | ending",
    "description": "descrição narrativa imersiva da cena (150–300 palavras)",
    "tone": "sombrio | épico | tenso | misterioso | trágico | heroico"
  },
  "game_state": {
    "player": {
      "hp": número inteiro (0 a 100),
      "status": ["normal", "ferido", "exausto", "em perigo", "morto"]
    }
  },
  "mechanics": {
    "danger_level": 1 a 5,
    "expected_damage": número inteiro (0 se não houver risco),
    "notes": "resumo curto da consequência mecânica da cena"
  },
  "choices": [
    {
      "id": "A",
      "label": "texto curto da escolha",
      "risk": "baixo | médio | alto"
    },
    {
      "id": "B",
      "label": "texto curto da escolha",
      "risk": "baixo | médio | alto"
    }
  ]
}

========================
REGRAS NARRATIVAS
========================
- A história DEVE ser contínua e lembrar das decisões anteriores.
- NUNCA ofereça escolhas que contradigam decisões já tomadas.
- Cada cena deve avançar a história de forma clara.
- Escolhas DEVEM ter consequências reais.
- Evite loops narrativos.
- Mantenha personagens, ambiente e tom consistentes.

========================
REGRAS DE COMBATE
========================
- Combate é uma CENA, não um sistema separado.
- Quando scene.type for "combat":
  - danger_level define a gravidade do inimigo ou ameaça.
  - expected_damage deve ser coerente com o perigo.
  - O jogador SEMPRE corre risco.
- Dano é aplicado pelo backend, não pelo texto.
- Se hp chegar a 0:
  - status deve incluir "morto"
  - scene.type deve ser "ending"

========================
REGRAS DE ESCOLHAS
========================
- Mínimo: 2 escolhas
- Máximo: 4 escolhas
- Escolhas devem ser:
  - curtas
  - mutuamente exclusivas
  - coerentes com a cena
- Cada escolha deve refletir claramente seu risco.

========================
REGRAS FINAIS
========================
- NÃO gere imagens.
- NÃO mencione sistemas, números ou cálculos no texto narrativo.
- NÃO repita escolhas anteriores.
- NÃO reinicie a história.
- A história deve ter começo, meio e fim possíveis.

IMPORTANTE:
Responda APENAS com o objeto JSON.
Nenhum texto antes ou depois.
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


def _parse_json_strict(content: str, current_hp: int = 100) -> Dict:
    """
    Tenta fazer o parse do JSON de forma inteligente com a nova estrutura.
    Primeiro tenta parse direto, depois procura por objeto JSON,
    e por último retorna fallback com estrutura completa.
    """
    # Tentativa 1: Parse direto
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "scene" in data and "choices" in data:
            return _validate_and_normalize(data, current_hp)
    except Exception:
        pass

    # Tentativa 2: Extrair último objeto JSON válido
    blob = _extract_last_json_object(content)
    if blob:
        try:
            data = json.loads(blob)
            if isinstance(data, dict) and "scene" in data and "choices" in data:
                return _validate_and_normalize(data, current_hp)
        except Exception:
            pass

    # Fallback: Retorna estrutura completa com o conteúdo como descrição
    return {
        "text": content.strip()[:500],
        "choices": ["Seguir adiante", "Investigar ao redor", "Recuar com cautela"],
        "scene_type": "narrative",
        "scene_tone": "misterioso",
        "game_state": {
            "player": {"hp": current_hp, "status": ["normal"]}
        },
        "mechanics": {
            "danger_level": 1,
            "expected_damage": 0,
            "notes": "Cena narrativa padrão"
        }
    }


def _validate_and_normalize(data: Dict, current_hp: int = 100) -> Dict:
    """
    Valida e normaliza a estrutura JSON retornada pela IA.
    🔥 CONVERTE CHOICES PARA STRINGS IMEDIATAMENTE 🔥
    """
    # Validar scene
    if "scene" not in data or not isinstance(data["scene"], dict):
        data["scene"] = {"type": "narrative", "description": "", "tone": "misterioso"}
    
    scene = data["scene"]
    scene_type = scene.get("type", "narrative")
    scene_description = scene.get("description", "")[:500]
    scene_tone = scene.get("tone", "misterioso")
    
    # Validar game_state
    if "game_state" not in data or not isinstance(data["game_state"], dict):
        data["game_state"] = {"player": {}}
    
    if "player" not in data["game_state"] or not isinstance(data["game_state"]["player"], dict):
        data["game_state"]["player"] = {}
    
    player = data["game_state"]["player"]
    player["hp"] = max(0, min(100, player.get("hp", current_hp)))
    
    status = player.get("status", [])
    if not isinstance(status, list) or not status:
        status = ["normal"]
    player["status"] = status
    
    # Se HP = 0, forçar status "morto" e type "ending"
    if player["hp"] == 0:
        if "morto" not in player["status"]:
            player["status"].append("morto")
        scene_type = "ending"
    
    # Validar mechanics
    if "mechanics" not in data or not isinstance(data["mechanics"], dict):
        data["mechanics"] = {}
    
    mechanics = data["mechanics"]
    mechanics["danger_level"] = max(1, min(5, mechanics.get("danger_level", 1)))
    mechanics["expected_damage"] = max(0, mechanics.get("expected_damage", 0))
    mechanics["notes"] = mechanics.get("notes", "")[:200]
    
    # 🔥 CONVERSÃO IMEDIATA: choices de dict para string 🔥
    raw_choices = data.get("choices", [])
    if not isinstance(raw_choices, list) or len(raw_choices) < 2:
        raw_choices = [
            {"label": "Seguir adiante"},
            {"label": "Investigar ao redor"}
        ]
    elif len(raw_choices) > 4:
        raw_choices = raw_choices[:4]
    
    # Extrair apenas os labels (strings)
    choices_strings = []
    for choice in raw_choices:
        if isinstance(choice, dict):
            label = choice.get("label", "")
            if label:
                choices_strings.append(label[:100])
            else:
                choices_strings.append("Opção desconhecida")
        else:
            choices_strings.append(str(choice)[:100])
    
    # Retornar estrutura normalizada COM CHOICES COMO STRINGS
    return {
        "text": scene_description,
        "choices": choices_strings,  # ✅ JÁ SÃO STRINGS AQUI
        "scene_type": scene_type,
        "scene_tone": scene_tone,
        "game_state": data["game_state"],
        "mechanics": mechanics,
    }


# ==========================================
# FUNÇÃO DE CHAMADA À IA
# ==========================================

async def _chat_once(user_prompt: str, current_hp: int = 100) -> Dict:
    """
    Faz uma chamada única à API da OpenRouter usando GPT-4o-mini.
    Retorna um dicionário com choices JÁ CONVERTIDAS PARA STRINGS.
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
                    "temperature": 0.8,
                    "max_tokens": 1000,
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

    response_data = response.json()
    content = response_data["choices"][0]["message"]["content"]
    
    # Parse retorna choices JÁ COMO STRINGS
    data = _parse_json_strict(content, current_hp)
    
    return data


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
    
    Returns:
        Dict com: index, text, choices (List[str]), model
    """
    
    # Obter HP atual do último estado
    current_hp = 100
    current_status = ["normal"]
    
    if history:
        last_state = history[-1].get("game_state", {}).get("player", {})
        current_hp = last_state.get("hp", 100)
        current_status = last_state.get("status", ["normal"])
    
    # Construir resumo do histórico
    recap = ""
    if history:
        recap = "📜 CONTEXTO DA HISTÓRIA:\n"
        recap += f"🩸 HP Atual: {current_hp}/100\n"
        recap += f"⚡ Status: {', '.join(current_status)}\n\n"
        recap += "🎬 EVENTOS RECENTES:\n"
        
        for h in history[-5:]:
            scene_type = h.get("scene_type", "narrative")
            description = h.get("text", "")[:200]
            chosen_idx = h.get("chosen_index")
            chosen_label = ""
            
            if chosen_idx is not None and "choices" in h:
                choices = h.get("choices", [])
                if isinstance(choices, list) and chosen_idx < len(choices):
                    chosen_label = f" → Escolha: '{choices[chosen_idx]}'"
            
            recap += f"• [{scene_type.upper()}] {description}{chosen_label}\n"
    
    # Construir prompt
    user_prompt = f"""
🎮 GERAÇÃO DE PRÓXIMA CENA DO RPG

📖 TEMA: {theme}
👤 PERSONAGEM: {character}

{recap}

🎯 TAREFA:
Gere a próxima cena da história considerando TUDO que aconteceu até agora.

IMPORTANTE:
- Mantenha continuidade total com os eventos anteriores
- Aplique as consequências das escolhas passadas
- Crie escolhas que façam sentido no contexto atual
- Mantenha o HP e status do personagem coerentes
- Se o personagem está ferido ou exausto, reflita isso na narrativa
- Avance a história de forma significativa
- Máximo de {max_choices} escolhas

LEMBRE-SE:
- NÃO repita escolhas já feitas
- NÃO ignore consequências anteriores
- NÃO crie loops narrativos
- Responda APENAS com o JSON no formato especificado
"""

    last_index = history[-1]["index"] + 1 if history else 0

    try:
        # Chamada à IA (já retorna choices como strings)
        result = await _chat_once(user_prompt, current_hp)
        
        # Garantir máximo de escolhas
        if len(result["choices"]) > max_choices:
            result["choices"] = result["choices"][:max_choices]
        
        # Retornar resposta compatível com Pydantic
        return {
            "index": last_index,
            "text": result["text"],
            "choices": result["choices"],  # ✅ JÁ SÃO STRINGS
            "model": MODEL,
            
            # Campos extras opcionais
            "scene_type": result.get("scene_type", "narrative"),
            "scene_tone": result.get("scene_tone", "misterioso"),
            "game_state": result.get("game_state", {"player": {"hp": current_hp, "status": current_status}}),
            "mechanics": result.get("mechanics", {"danger_level": 1, "expected_damage": 0, "notes": ""}),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Serviço de IA indisponível: {type(e).__name__} - {str(e)}"
        )


# ==========================================
# INFORMAÇÕES DO MODELO
# ==========================================

def get_model_info() -> Dict:
    """Retorna informações sobre o modelo atual."""
    return {
        "model": MODEL,
        "provider": "OpenRouter",
        "base_model": "OpenAI GPT-4o-mini",
        "context_window": "128k tokens",
        "pricing": {
            "input": "$0.15 per 1M tokens",
            "output": "$0.60 per 1M tokens"
        },
        "features": {
            "game_state_management": True,
            "combat_system": True,
            "consequence_tracking": True,
            "dynamic_difficulty": True
        }
    }