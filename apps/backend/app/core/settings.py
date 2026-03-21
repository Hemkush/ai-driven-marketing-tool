from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    frontend_url: str = "http://localhost:5173"
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://us.api.openai.com/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/test_db"
    app_env: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
