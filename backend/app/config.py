from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'mysql+pymysql://sgwa:sgwa_local_dev@127.0.0.1:3307/sgwa'
    jwt_secret: str = Field(min_length=32)
    trusted_origins: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']
    cookie_secure: bool = False
    model_dir: Path = Path('ml/artifacts')
    demo_password: str = Field(default='', repr=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
