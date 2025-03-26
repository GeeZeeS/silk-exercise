import os

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """MongoDB database configuration"""

    host: str = Field(default=os.environ.get("MONGO_HOST", "localhost"))
    port: str = Field(default=os.environ.get("MONGO_PORT", "27017"))
    user: str = Field(default=os.environ.get("MONGODB_USER", ""))
    password: str = Field(default=os.environ.get("MONGO_PASSWORD", ""))
    database: str = Field(default=os.environ.get("MONGODB_DB", "silk_db"))


class Settings(BaseModel):
    """Application settings"""

    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    app_name: str = Field(default=os.environ.get("APP_NAME", "Silk Exercise"))
    environment: str = Field(default=os.environ.get("ENVIRONMENT", "development"))

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
