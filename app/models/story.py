from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from typing import Optional, Dict, Any

# entrada para iniciar a história
class StartStoryIn(BaseModel):
    theme_prompt: str = Field(min_length=3, description="Prompt do tema")
    character_prompt: str = Field(min_length=3, description="Prompt do personagem")
    initial_choices: int = Field(2, ge=2, le=4, description="Qtd inicial de escolhas (2 a 4)")

# saída padrão de um passo da história
class StepOut(BaseModel):
    story_id: str
    step_id: str
    index: int
    text: str
    choices: List[str]  # 2..4 escolhas
    created_at: datetime

# entrada para escolher um caminho
class ChooseIn(BaseModel):
    choice_index: int = Field(ge=0, description="Índice da escolha (0-based)")

# metadados completos da história
class StoryMetaOut(BaseModel):
    story_id: str
    owner_uid: str
    theme_prompt: str
    character_prompt: str
    created_at: datetime
    updated_at: datetime
    status: str
    current_step_id: Optional[str] = None

# listagem resumida
class StorySummaryOut(BaseModel):
    story_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    last_text: Optional[str] = None


class StepOut(BaseModel):
    story_id: str
    step_id: str
    index: int
    text: str
    choices: List[str]
    created_at: datetime

    # 🔥 NOVO CAMPO (opcional, não quebra nada)
    state: Optional[Dict[str, Any]] = None