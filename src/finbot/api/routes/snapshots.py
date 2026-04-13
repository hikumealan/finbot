"""Net worth snapshot history endpoints."""
from fastapi import APIRouter

from finbot.api.deps import CurrentUser, DbSession
from finbot.models.snapshot import Snapshot

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


@router.get("")
def list_snapshots(db: DbSession, _user: CurrentUser):
    snaps = db.query(Snapshot).order_by(Snapshot.date).all()
    return [{"date": str(s.date), "net_worth": float(s.net_worth), "total_assets": float(s.total_assets), "total_liabilities": float(s.total_liabilities)} for s in snaps]
