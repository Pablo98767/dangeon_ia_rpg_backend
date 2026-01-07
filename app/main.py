from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, auth, users
from app.routers import stories
from app.routers import pix
from app.routers import coins
from app.routers import webhooks  # ← ADICIONE ESTE IMPORT

def create_app() -> FastAPI:
    # 1. Removida a duplicidade: declaramos o app apenas uma vez
app.add_middleware(
    CORSMiddleware,
    # Em vez de misturar os dois, vamos focar no que funciona para o navegador
    allow_origins=[
        "http://localhost:3000",
        "https://dungeon-generator-frontend.onrender.com",
        "https://dungeon-ia-master.lovable.app",
    ],
    # A regex deve ser usada apenas se o allow_origins não for suficiente
    allow_origin_regex=r"https://.*\.lovable\.app|https://.*\.gptengineer\.run",
    allow_credentials=True,
    allow_methods=["*"],  # Garante que OPTIONS, POST, GET sejam aceitos
    allow_headers=["*"],  # Garante que Authorization e Content-Type sejam aceitos
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
