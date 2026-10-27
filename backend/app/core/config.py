from typing import List, Union
from pathlib import Path
import json
import urllib.parse
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "InsightFlow AI API"
    VERSION: str = "1.0.0"

    # MySQL Configuration
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "insightflow_db"

    # Database URL
    DATABASE_URL: str = ""

    # Google Gemini API Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Security, Authentication & Rate Limiting
    ENABLE_API_KEY_AUTH: bool = False
    API_AUTH_KEY: str = ""
    MAX_REQUEST_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB general JSON body limit
    RATE_LIMIT_PER_MINUTE: int = 120

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    return json.loads(v_trimmed)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        encoded_password = urllib.parse.quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{encoded_password}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    model_config = SettingsConfigDict(
        env_file=(str(ENV_PATH), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
