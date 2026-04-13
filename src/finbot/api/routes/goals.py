"""Goal management endpoints."""
from fastapi import APIRouter, HTTPException

from finbot.analysis.goals import compute_goal_progress
from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import GoalCreate, GoalOut
from finbot.models.goal import Goal

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("", response_model=list[GoalOut])
def list_goals(db: DbSession, _user: CurrentUser):
    progress = compute_goal_progress(db)
    goals = db.query(Goal).all()
    progress_map = {p.name: p for p in progress}
    result = []
    for g in goals:
        p = progress_map.get(g.name)
        result.append(GoalOut(
            id=g.id, name=g.name, goal_type=g.goal_type,
            target_amount=float(g.target_amount), current_amount=float(g.current_amount),
            target_date=g.target_date,
            progress_pct=p.progress_pct if p else 0,
            monthly_needed=p.monthly_needed if p else 0,
            status=p.status if p else "on_track",
        ))
    return result


@router.post("", response_model=GoalOut)
def create_goal(body: GoalCreate, db: DbSession, _user: CurrentUser):
    g = Goal(name=body.name, goal_type=body.goal_type, target_amount=body.target_amount, current_amount=body.current_amount, target_date=body.target_date)
    db.add(g)
    db.commit()
    db.refresh(g)
    return GoalOut(id=g.id, name=g.name, goal_type=g.goal_type, target_amount=float(g.target_amount), current_amount=float(g.current_amount), target_date=g.target_date)


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, body: GoalCreate, db: DbSession, _user: CurrentUser):
    g = db.query(Goal).get(goal_id)
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(g, field, val)
    db.commit()
    db.refresh(g)
    return GoalOut(id=g.id, name=g.name, goal_type=g.goal_type, target_amount=float(g.target_amount), current_amount=float(g.current_amount), target_date=g.target_date)


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, db: DbSession, _user: CurrentUser):
    g = db.query(Goal).get(goal_id)
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(g)
    db.commit()
    return {"status": "deleted"}
