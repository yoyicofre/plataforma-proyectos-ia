import os
from urllib.parse import quote_plus

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Project Template")
    environment: str = os.getenv("ENVIRONMENT", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "plataformaIa")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "plataforma-ia")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "plataforma-ia-api")
    jwt_exp_minutes: int = int(os.getenv("JWT_EXP_MINUTES", "480"))
    dev_bootstrap_key: str = os.getenv("DEV_BOOTSTRAP_KEY", "dev-bootstrap-key")
    portal_access_key: str = os.getenv("PORTAL_ACCESS_KEY", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model_text: str = os.getenv("OPENAI_MODEL_TEXT", "gpt-5.2")
    openai_model_image: str = os.getenv("OPENAI_MODEL_IMAGE", "gpt-image-1")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model_text: str = os.getenv("GEMINI_MODEL_TEXT", "gemini-3-pro-preview")
    gemini_model_image: str = os.getenv("GEMINI_MODEL_IMAGE", "gemini-3-pro-image-preview")
    gemini_base_url: str = os.getenv(
        "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
    )

    openai_text_input_cost_per_1k: float = float(os.getenv("OPENAI_TEXT_INPUT_COST_PER_1K", "0"))
    openai_text_output_cost_per_1k: float = float(
        os.getenv("OPENAI_TEXT_OUTPUT_COST_PER_1K", "0")
    )
    gemini_text_input_cost_per_1k: float = float(os.getenv("GEMINI_TEXT_INPUT_COST_PER_1K", "0"))
    gemini_text_output_cost_per_1k: float = float(
        os.getenv("GEMINI_TEXT_OUTPUT_COST_PER_1K", "0")
    )
    openai_image_cost_per_image: float = float(os.getenv("OPENAI_IMAGE_COST_PER_IMAGE", "0"))
    gemini_image_cost_per_image: float = float(os.getenv("GEMINI_IMAGE_COST_PER_IMAGE", "0"))

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"prod", "production"}

    @property
    def database_url(self) -> str:
        override = os.getenv("DATABASE_URL")
        if override:
            return override
        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def validate_runtime_security(self) -> None:
        if not self.is_production:
            return

        insecure_jwt_values = {"", "change-this-secret"}
        if self.jwt_secret in insecure_jwt_values or len(self.jwt_secret) < 32:
            raise ValueError(
                "Invalid JWT_SECRET for production. Use a non-default value with at least 32 chars."
            )

        if self.dev_bootstrap_key == "dev-bootstrap-key":
            raise ValueError("DEV_BOOTSTRAP_KEY default value is not allowed in production.")

        if len(self.portal_access_key) < 12:
            raise ValueError("PORTAL_ACCESS_KEY must be set with at least 12 chars in production.")


settings = Settings()
settings.validate_runtime_security()
