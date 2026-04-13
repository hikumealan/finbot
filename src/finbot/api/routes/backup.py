"""Backup and restore endpoints."""
import shutil
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile

from finbot.api.deps import CurrentUser
from finbot.config import settings

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.post("")
def create_backup(_user: CurrentUser):
    settings.ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = settings.backups_dir / f"finbot_backup_{ts}.db"
    shutil.copy2(settings.db_path, dest)
    return {"status": "ok", "file": str(dest), "size": dest.stat().st_size}


@router.get("/list")
def list_backups(_user: CurrentUser):
    if not settings.backups_dir.exists():
        return []
    backups = sorted(settings.backups_dir.glob("*.db"), reverse=True)
    return [{"name": b.name, "size": b.stat().st_size, "modified": str(datetime.fromtimestamp(b.stat().st_mtime))[:19]} for b in backups]


@router.delete("/{filename}")
def delete_backup(filename: str, _user: CurrentUser):
    path = settings.backups_dir / filename
    if not path.exists() or not path.name.endswith(".db"):
        raise HTTPException(status_code=404, detail="Backup not found")
    path.unlink()
    return {"status": "deleted"}


@router.post("/restore")
async def restore_backup(file: UploadFile, _user: CurrentUser):
    data = await file.read()
    if len(data) > 500 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 500 MB)")
    if not data[:16].startswith(b"SQLite format 3"):
        raise HTTPException(status_code=400, detail="Invalid file — not a SQLite database")

    settings.ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre = settings.backups_dir / f"pre_restore_{ts}.db"
    if settings.db_path.exists():
        shutil.copy2(settings.db_path, pre)
    with open(settings.db_path, "wb") as f:
        f.write(data)
    return {"status": "restored", "pre_restore_backup": str(pre)}
