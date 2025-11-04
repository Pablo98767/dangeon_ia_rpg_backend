from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = Field("fastapi-firebase", alias="APP_NAME")
    app_env: str = Field("dev", alias="APP_ENV")
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")

    firebase_project_id: str = Field(..., alias="FIREBASE_PROJECT_ID")
    firebase_api_key: str = Field(..., alias="FIREBASE_API_KEY")

    # Novo: caminho para o JSON
    firebase_credentials_file: str | None = Field(None, alias="FIREBASE_CREDENTIALS_FILE")

    # Campos abaixo ficam opcionais (apenas se não usar arquivo)
    firebase_client_email: str | None = Field(None, alias="FIREBASE_CLIENT_EMAIL")
    firebase_private_key: str | None = Field(None, alias="FIREBASE_PRIVATE_KEY")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
