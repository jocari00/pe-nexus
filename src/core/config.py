"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """PE-Nexus application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "PE-Nexus"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # LLM Provider Selection
    # Options: "anthropic", "groq", "ollama", "none"
    llm_provider: str = Field(
        default="groq",
        description="LLM provider to use: anthropic, groq, ollama, or none"
    )

    # Anthropic (Claude) API
    anthropic_api_key: str = Field(default="", description="Anthropic API key for Claude")
    claude_model: str = "claude-sonnet-4-20250514"

    # Groq API (FREE - Llama 3, Mixtral)
    groq_api_key: str = Field(default="", description="Groq API key (free tier available)")
    groq_model: str = "llama-3.3-70b-versatile"  # Free, fast, good quality

    # Ollama (Local - completely free)
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = "llama3.2"  # or "mistral", "codellama", etc.

    # Common LLM settings
    max_tokens: int = 4096

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider selection."""
        valid_providers = ["anthropic", "groq", "ollama", "none"]
        if v.lower() not in valid_providers:
            raise ValueError(f"llm_provider must be one of: {valid_providers}")
        return v.lower()

    @property
    def active_llm_provider(self) -> Optional[str]:
        """Get the active LLM provider based on configuration."""
        if self.llm_provider == "none":
            return None
        if self.llm_provider == "anthropic" and self.anthropic_api_key:
            return "anthropic"
        if self.llm_provider == "groq" and self.groq_api_key:
            return "groq"
        if self.llm_provider == "ollama":
            return "ollama"
        # Fallback: try groq, then anthropic, then ollama
        if self.groq_api_key:
            return "groq"
        if self.anthropic_api_key:
            return "anthropic"
        return None  # No LLM available

    @property
    def active_model_name(self) -> str:
        """Get the model name for the active provider."""
        provider = self.active_llm_provider
        if provider == "anthropic":
            return self.claude_model
        if provider == "groq":
            return self.groq_model
        if provider == "ollama":
            return self.ollama_model
        return "none"

    @property
    def llm_display_name(self) -> str:
        """Human-readable name for the active LLM."""
        provider = self.active_llm_provider
        if provider == "anthropic":
            return f"Claude ({self.claude_model})"
        if provider == "groq":
            return f"Llama 3 via Groq ({self.groq_model})"
        if provider == "ollama":
            return f"Ollama Local ({self.ollama_model})"
        return "None (Rule-based only)"

    # Database
    database_url: str = "sqlite+aiosqlite:///./pe_nexus.db"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "pe_nexus_docs"

    # Agent Settings
    agent_max_iterations: int = 10
    agent_timeout_seconds: int = 300

    # PDF Processing
    pdf_extraction_confidence_threshold: float = 0.7
    pdf_max_pages: int = 500

    # External APIs (optional)
    fred_api_key: str = ""
    newsapi_key: str = ""

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://localhost:8501"],
        description="Allowed CORS origins. Use ['*'] only for development.",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )

    @field_validator("cors_origins", "cors_allow_credentials", mode="after")
    @classmethod
    def validate_cors_security(cls, v, info):
        """Warn about insecure CORS configuration."""
        if info.field_name == "cors_origins" and "*" in v:
            import logging
            logging.getLogger(__name__).warning(
                "CORS configured with wildcard origin '*'. "
                "This is insecure for production - set specific origins."
            )
        return v

    @property
    def base_dir(self) -> Path:
        """Get the base directory of the project."""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get the data directory."""
        data_path = self.base_dir / "data"
        data_path.mkdir(exist_ok=True)
        return data_path

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.database_url.lower()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
