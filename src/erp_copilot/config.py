from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.7


@lru_cache
def get_settings() -> Settings:
    return Settings()


class PineconeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    pinecone_api_key: str
    pinecone_index: str = "erp-knowledge"
    pinecone_namespace: str = "docs"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_embed_model: str = "llama-text-embed-v2"


def pinecone_configured() -> bool:
    try:
        PineconeSettings()
    except ValueError:
        return False
    return True
