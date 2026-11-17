import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "JinwooCrawl")
    APP_ENV: str = os.getenv("APP_ENV", "local")
    PORT: int = int(os.getenv("PORT", "5002"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # CORS
    raw_cors: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5001,http://127.0.0.1:5001,https://crawl.jinwoostream.lol"
    )
    CORS_ORIGINS: list[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "jinwoo-crawl")
    MONGODB_COLLECTION: str = os.getenv("MONGODB_COLLECTION", "api")

    # Scraper Credentials
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")
    TIKTOK_SESSION_KEY: str = os.getenv("TIKTOK_SESSION_KEY", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    META_ACCESS_TOKEN: str = os.getenv("META_ACCESS_TOKEN", "")

settings = Settings()
