from fastapi import FastAPI
from app.core.config import settings
from app.routers import health, auth, users
from app.routers import stories  # << novo

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.get("/")
    def root():
        return {"message": f"Bem-vindo à API Backend do APP D&D"}

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(stories.router)  # << novo
    return app

app = create_app()
