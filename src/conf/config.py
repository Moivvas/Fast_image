from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    sqlalchemy_database_url: str = 'postgresql+psycopg2://user:password@localhost:5432/postgres'
    secret_key: str = 'secret_key'
    algorithm: str = 'HS256'
    redis_host: str = 'localhost'
    redis_port: int = 6379
    postgres_db: str = 'db'
    postgres_user: str = 'some_user'
    postgres_password: str = 'password'
    postgres_port: int = '8000'
    cloudinary_name: str = 'Cloudinary'
    cloudinary_api_key: int = '12903053'
    cloudinary_api_secret: str = 'secret'
   

settings = Settings()
