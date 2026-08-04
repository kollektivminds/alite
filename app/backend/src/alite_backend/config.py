"""creates and sets system settings for pydantic

This module...
"""

from pathlib import Path
from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",
    )

    # --- Core Application Environment ---
    ENV_MODE: str = Field(
        ..., description="Operating mode: development, test, or production"
    )
    NAMESPACE: str = Field(..., description="Application deployment namespace")
    APP_DIR: str = Field(..., description="Absolute application working directory")

    # --- Database Credentials & Identifiers (Loaded from .env) ---
    DB_USER: str = Field(..., description="PostgreSQL database username")
    DB_PW: SecretStr = Field(..., description="PostgreSQL database password (masked)")
    DB_HOST: str = Field(..., description="PostgreSQL database hostname/service name")
    DB_PORT: int = Field(5432, description="PostgreSQL database port")
    DB_NAME: str = Field(..., description="Production database name")
    DEV_DB_NAME: str = Field(..., description="Development database name")
    TEST_DB_NAME: str = Field(..., description="Testing/Pytest database name")

    # --- External Integrations & Storage Paths ---
    CANVAS_TOKEN: str = Field(..., description="LMS Canvas API access token")
    LOG_LOC: str = Field(..., description="System logging directory path")
    VOCAB_LIST_LOC: str = Field(..., description="Linguistic corpus data path")
    VOCAB_CACHE_LOC: str = Field(..., description="Statistical cache directory path")
    VITE_API_BASE_URL: str = Field(
        ..., description="React frontend connection base URL"
    )

    # Computed Database URL (as a property)
    @computed_field
    @property
    def PROD_DATABASE_URL(self) -> str:
        """Constructs and returns the production PostgreSQL connection URI."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PW.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @computed_field
    @property
    def DEV_DATABASE_URL(self) -> str:
        """Constructs and returns the development PostgreSQL connection URI."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PW.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DEV_DB_NAME}"
        )

    @computed_field
    @property
    def TEST_DATABASE_URL(self) -> str:
        """Constructs and returns the test PostgreSQL connection URI for pytest suites."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PW.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.TEST_DB_NAME}"
        )


# Instantiate the settings once for the entire application
settings = Settings()  # type: ignore
