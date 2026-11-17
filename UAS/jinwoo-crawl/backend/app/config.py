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
    BACKEND_DOMAIN: str = os.getenv("BACKEND_DOMAIN", "https://scrape.jinwoostream.lol")
    FRONTEND_DOMAIN: str = os.getenv("FRONTEND_DOMAIN", "https://crawl.jinwoostream.lol")
    CHROMIUM_EXECUTABLE_PATH: str = os.getenv("CHROMIUM_EXECUTABLE_PATH", "")

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
    # Cookie 'sessionid' dari browser yang sudah login Instagram (lebih andal daripada login password)
    INSTAGRAM_SESSIONID: str = os.getenv("INSTAGRAM_SESSIONID", "")
    # Cookie 'c_user' & 'xs' atau kredensial login Facebook (opsional)
    FACEBOOK_C_USER: str = os.getenv("FACEBOOK_C_USER", "")
    FACEBOOK_XS: str = os.getenv("FACEBOOK_XS", "")
    FACEBOOK_EMAIL: str = os.getenv("FACEBOOK_EMAIL", "")
    FACEBOOK_PASSWORD: str = os.getenv("FACEBOOK_PASSWORD", "")
    TIKTOK_USERNAME: str = os.getenv("TIKTOK_USERNAME", "")
    TIKTOK_PASSWORD: str = os.getenv("TIKTOK_PASSWORD", "")
    TIKTOK_SESSION_KEY: str = os.getenv("TIKTOK_SESSION_KEY", "")
    TIKTOK_MS_TOKEN: str = os.getenv("TIKTOK_MS_TOKEN", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    META_ACCESS_TOKEN: str = os.getenv("META_ACCESS_TOKEN", "")

settings = Settings()
