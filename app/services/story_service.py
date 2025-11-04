from uuid import uuid4
from datetime import datetime

# Simulação de banco de dados em memória
STORIES = {}
STEPS = {}

class StoryService:
    def new_story(self, uid, theme, character):
        story_id = str(uuid4())
        STORIES[story_id] = {
            "story_id": story_id,
            "owner_uid": uid,
            "theme_prompt": theme,
            "character_prompt": character,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "current_step_id": None,
        }
        return story_id  # ✅ retorna string válida

    def add_step(self, story_id, index, text, choices):
        step_id = str(uuid4())
        STEPS[step_id] = {
            "step_id": step_id,
            "story_id": story_id,
            "index": index,
            "text": text,
            "choices": choices,
            "created_at": datetime.utcnow(),
        }
        STORIES[story_id]["current_step_id"] = step_id
        STORIES[story_id]["updated_at"] = datetime.utcnow()
        return step_id  # ✅ retorna string válida

    def get_story(self, story_id):
        return STORIES.get(story_id)

    def get_step(self, story_id, step_id):
        step = STEPS.get(step_id)
        if step and step["story_id"] == story_id:
            return step
        return None

    def choose(self, story_id, step_id, choice_index):
        pass

    def recent_history(self, story_id, k=10):
        steps = [s for s in STEPS.values() if s["story_id"] == story_id]
        return sorted(steps, key=lambda s: s["index"])[-k:]

    def list_user_stories(self, uid, limit=50):
        return [s for s in STORIES.values() if s["owner_uid"] == uid][:limit]

S = StoryService()
