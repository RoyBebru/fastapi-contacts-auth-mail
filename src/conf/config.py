from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    secret_key: str = "HERO_SECRET_KEY"

    mail_username: str = "HERO@meta.ua"
    mail_password: str = "HERO_MAIL_PASSWORD"
    mail_from: str = "HERO@meta.ua"
    mail_port: int = 465
    mail_server: str = "smtp.meta.ua"
    mail_from_name: str = "HERO@meta.ua"

    postgresql_db: str = "HERO_DB_NAME"
    postgresql_user: str = "HERO_DB_USER_NAME"
    postgresql_password: str = "HERO_DB_USER_PASSWORD"
    postgresql_host: str = "HERO_DB_HOST"
    postgresql_port: int = 5432

    redis_host: str = "localhost"
    redis_port: int = 6379

    cloudinary_name: str = "HERO_CLOUDINARY_NAME"
    cloudinary_api_key: str = "HERO_CLOUDINARY_API_KEY"
    cloudinary_api_secret: str = "HERO_CLOUDINARY_API_SECRET"

    model_config = ConfigDict(extra='ignore', env_file=".env", env_file_encoding="utf-8")

settings = Settings()
