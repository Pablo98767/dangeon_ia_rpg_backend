from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers import health, auth, users
from routers import stories
from routers import pix
from routers import coins
from routers import webhooks  # ← ADICIONE ESTE IMPORT

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # Configurar CORS para permitir requisições do frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",      # React dev server
            "http://127.0.0.1:3000",      # React dev server alternativo
        ],
        allow_credentials=True,
        allow_methods=["*"],              # Permite todos os métodos (GET, POST, OPTIONS, etc)
        allow_headers=["*"],              # Permite todos os headers
    )

    @app.get("/")
    def root():
        return {"message": f"Bem-vindo à API Backend do APP D&D"}

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(stories.router)
    app.include_router(pix.router)
    app.include_router(coins.router)
    app.include_router(webhooks.router)  # ← ADICIONE ESTA LINHA

    return app

app = create_app()
