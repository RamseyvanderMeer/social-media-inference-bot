"""Configuration management using Pydantic settings."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class GrokSettings(BaseSettings):
    """Grok API configuration."""

    api_key: str = Field(..., alias="GROK_API_KEY")
    api_base_url: str = Field(
        default="https://api.x.ai/v1", alias="GROK_API_BASE_URL"
    )
    model: str = Field(default="grok-beta", alias="GROK_MODEL")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000)
    timeout: int = Field(default=60)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is provided."""
        if not v or v == "your_grok_api_key_here":
            raise ValueError("GROK_API_KEY must be set in environment or .env file")
        return v


class VectorStoreSettings(BaseSettings):
    """Vector store configuration."""

    db_path: Path = Field(default=Path("./data/chroma_db"), alias="CHROMA_DB_PATH")
    collection_name: str = Field(
        default="x_data", alias="CHROMA_COLLECTION_NAME"
    )
    embedding_model: str = Field(default="text-embedding-3-small")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("db_path", mode="before")
    @classmethod
    def validate_db_path(cls, v: str | Path) -> Path:
        """Convert string to Path and ensure parent directory exists."""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class AgentSettings(BaseSettings):
    """Agent loop configuration."""

    max_iterations: int = Field(default=10, alias="MAX_ITERATIONS")
    timeout: int = Field(default=300, alias="AGENT_TIMEOUT")
    context_window_size: int = Field(default=10, alias="CONTEXT_WINDOW_SIZE")
    enable_replanning: bool = Field(default=True)
    replanning_confidence_threshold: float = Field(default=0.6)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v: int) -> int:
        """Validate max iterations is positive."""
        if v <= 0:
            raise ValueError("MAX_ITERATIONS must be positive")
        return v

    @field_validator("replanning_confidence_threshold")
    @classmethod
    def validate_confidence_threshold(cls, v: float) -> float:
        """Validate confidence threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(
                "replanning_confidence_threshold must be between 0 and 1"
            )
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[Path] = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()


class Settings(BaseSettings):
    """Main settings class combining all configuration sections."""

    grok: GrokSettings = Field(default_factory=GrokSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings
