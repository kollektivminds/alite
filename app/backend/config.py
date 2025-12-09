"""creates and sets system settings for pydantic
    
    This module...
"""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='forbid'
    )

    # Database Settings (from .env)
    ENV_MODE: str
    DB_USER: str
    DB_PW: SecretStr
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    CANVAS_TOKEN: str
    APP_DIR: str
    LOG_LOC: str
    VOCAB_LIST_LOC: str

    # Computed Database URL (as a property)
    @property
    def DATABASE_URL(self) -> str:
        # SecretStr needs .get_secret_value() to expose the string
        return f"postgresql://{self.DB_USER}:{self.DB_PW.get_secret_value()}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Instantiate the settings once for the entire application
settings = Settings() # type: ignore