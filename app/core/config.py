from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = Field("fastapi-firebase", alias="APP_NAME")
    app_env: str = Field("dev", alias="APP_ENV")
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8000, alias="APP_PORT")
    
    firebase_project_id: str = Field(..., alias="FIREBASE_PROJECT_ID")
    firebase_api_key: str = Field(..., alias="FIREBASE_API_KEY")
    firebase_credentials_file: str | None = Field(None, alias="FIREBASE_CREDENTIALS_FILE")
    firebase_credentials_json: str | None = Field(None, alias="FIREBASE_CREDENTIALS_JSON")
    firebase_client_email: str | None = Field(None, alias="FIREBASE_CLIENT_EMAIL")
    firebase_private_key: str | None = Field(None, alias="FIREBASE_PRIVATE_KEY")
    
    # ============ STRIPE CONFIGURATION ============
    stripe_secret_key: str = Field(..., alias="STRIPE_SECRET_KEY")
    stripe_publishable_key: str = Field(..., alias="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: str = Field(..., alias="STRIPE_WEBHOOK_SECRET")
    stripe_success_url: str = Field(
        "http://localhost:8080/payment/success?session_id={CHECKOUT_SESSION_ID}",
        alias="STRIPE_SUCCESS_URL"
    )
    stripe_cancel_url: str = Field(
        "https://dungeon-master-console.onrender.com/dashboard",
        alias="STRIPE_CANCEL_URL"
    )
    # ==============================================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Não dá erro se .env não existir
        _env_file_sentinel=None
    )

settings = Settings()
