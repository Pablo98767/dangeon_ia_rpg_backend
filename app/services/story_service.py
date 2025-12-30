from uuid import uuid4
from datetime import datetime
from app.services.firebase_admin_svc import firestore_client

class StoryService:
    def __init__(self):
        self.db = firestore_client()

    def new_story(self, uid, theme, character):
        story_id = str(uuid4())
        story_data = {
            "story_id": story_id,
            "owner_uid": uid,
            "theme_prompt": theme,
            "character_prompt": character,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "current_step_id": None,
        }

        self.db.collection("stories").document(story_id).set(story_data)
        return story_id

    def add_step(self, story_id, index, text, choices):
        step_id = str(uuid4())
        step_data = {
            "step_id": step_id,
            "story_id": story_id,
            "index": index,
            "text": text,
            "choices": choices,
            "created_at": datetime.utcnow(),
        }

        self.db.collection("stories").document(story_id).collection("steps").document(step_id).set(step_data)
        self.db.collection("stories").document(story_id).update({
            "current_step_id": step_id,
            "updated_at": datetime.utcnow()
        })

        return step_id

    def get_story(self, story_id):
        doc = self.db.collection("stories").document(story_id).get()
        return doc.to_dict() if doc.exists else None

    def get_step(self, story_id, step_id):
        doc = self.db.collection("stories").document(story_id).collection("steps").document(step_id).get()
        return doc.to_dict() if doc.exists else None

    def choose(self, story_id, step_id, choice_index):
        # Aqui você pode implementar a lógica de IA e persistência do novo passo
        pass

    def recent_history(self, story_id, k=10):
        steps_ref = self.db.collection("stories").document(story_id).collection("steps")
        query = steps_ref.order_by("index").limit_to_last(k)
        return [doc.to_dict() for doc in query.get()]  # ✅ Correção aplicada aqui

    def list_user_stories(self, uid, limit=50):
        query = self.db.collection("stories").where("owner_uid", "==", uid).order_by("created_at", direction="DESCENDING").limit(limit)
        return [doc.to_dict() for doc in query.stream()]
  
   
    def list_steps(self, story_id):
        steps_ref = self.db.collection("stories").document(story_id).collection("steps")
        query = steps_ref.order_by("index")
        return [doc.to_dict() for doc in query.stream()]



S = StoryService()
