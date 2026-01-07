from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, auth, users
from app.routers import stories
from app.routers import pix
from app.routers import coins
from app.routers import webhooks  # ← ADICIONE ESTE IMPORT
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, auth, users, stories, pix, coins, webhooks

def create_app() -> FastAPI:
    # 1. Instância única do FastAPI
    app = FastAPI(title=settings.app_name)

    # 2. Configuração de CORS (com recuo de 4 espaços)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://dungeon-generator-frontend.onrender.com",
            "https://dungeon-ia-master.lovable.app",
            "https://dungeon-generator.lovable.app",  # ← SEU NOVO LINK AQUI
        ],
        allow_origin_regex=r"https://.*\.lovable\.app|https://.*\.gptengineer\.run",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Inclusão das rotas (Routers)
    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(users.router, prefix="/users", tags=["Users"])
    app.include_router(stories.router, prefix="/stories", tags=["Stories"])
    app.include_router(pix.router, prefix="/pix", tags=["PIX"])
    app.include_router(coins.router, prefix="/coins", tags=["Coins"])
    app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

    return app

# 4. Criação da instância global que o Render/Uvicorn vai rodar
app = create_app()

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
