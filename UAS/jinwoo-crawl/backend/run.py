import os
from pathlib import Path
import uvicorn
from app.config import settings


def _ensure_safe_tmpdir() -> None:
    cur_tmp = os.environ.get("TMPDIR", "").strip()
    if not cur_tmp or not Path(cur_tmp).is_dir():
        safe_tmp = Path(__file__).resolve().parent.parent / ".pw-tmp"
        safe_tmp.mkdir(parents=True, exist_ok=True)
        os.environ["TMPDIR"] = os.environ["TEMP"] = os.environ["TMP"] = str(safe_tmp)


if __name__ == "__main__":
    _ensure_safe_tmpdir()
    is_local = settings.APP_ENV.strip().lower() == "local"
    print(f"Starting {settings.APP_NAME} Backend ({settings.APP_ENV}) on {settings.HOST}:{settings.PORT}...", flush=True)
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=is_local,
        workers=1,
        log_level="info",
    )
