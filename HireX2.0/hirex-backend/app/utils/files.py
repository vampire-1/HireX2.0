import shutil
from pathlib import Path
from fastapi import UploadFile
from ..config import settings

def save_upload(file: UploadFile) -> str:
    dest = Path(settings.RESUME_DIR) / file.filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return str(dest)
