"""Configuration management for voice assistant."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用程式配置。"""

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
