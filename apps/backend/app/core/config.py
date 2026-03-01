import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://us.api.openai.com/v1")

    def validate_openai(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Set it in apps/backend/.env"
            )

settings = Settings()
