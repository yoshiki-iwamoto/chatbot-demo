from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.ai.sakura.ad.jp/v1"
    LLM_MODEL: str = "gpt-oss-120b"
    EMBEDDING_MODEL: str = "multilingual-e5-large"
    APP_SECRET_KEY: str = "dev-secret-key"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/chatbot.db"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
