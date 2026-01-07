from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, auth, users
from app.routers import stories
from app.routers import pix
from app.routers import coins
from app.routers import webhooks


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # ============================================
    # CONFIGURAÇÃO CORS CORRIGIDA ✅
    # ============================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            # Desenvolvimento - React (Create React App)
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            
            # Desenvolvimento - React/Vue com VITE (porta padrão 5173) ✅✅✅
            "http://localhost:5173",      # ✅ ADICIONE ESTA LINHA!
            "http://127.0.0.1:5173",      # ✅ ADICIONE ESTA LINHA!
            
            # Desenvolvimento - Vue/outros (porta 8080)
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            
            # Produção
            "https://dungeon-generator-frontend.onrender.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],              # Permite GET, POST, OPTIONS, etc
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
    app.include_router(webhooks.router)

    return app

app = create_app()