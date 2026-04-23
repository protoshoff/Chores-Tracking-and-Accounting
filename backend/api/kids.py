from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Chore, ChoreLog, ChoreStatus
from ..services.chores import ChoreService

router = APIRouter(prefix="/api/kids", tags=["Kids"])

from pydantic import BaseModel

class KidWithSummary(BaseModel):
    id: int
    name: str
    balance: float
    allowance: float
    avatar_path: str
    chores_summary: dict

@router.get("/", response_model=List[KidWithSummary])
def list_kids(session: Session = Depends(get_session)):
    kids = session.exec(select(User).where(User.is_active == True)).all()
    service = ChoreService(session)
    
    result = []
    for k in kids:
        summary = service.calculate_weekly_progress(k.id)
        result.append(KidWithSummary(
            id=k.id, 
            name=k.name, 
            balance=k.balance,
            allowance=k.allowance,
            avatar_path=k.avatar_path,
            chores_summary=summary
        ))
        
    return result

@router.get("/{kid_id}", response_model=KidWithSummary)
def get_kid(kid_id: int, session: Session = Depends(get_session)):
    kid = session.get(User, kid_id)
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")
        
    service = ChoreService(session)
    summary = service.calculate_weekly_progress(kid.id)
    return KidWithSummary(
        id=kid.id,
        name=kid.name,
        balance=kid.balance,
        allowance=kid.allowance,
        avatar_path=kid.avatar_path,
        chores_summary=summary
    )

@router.get("/{kid_id}/progress-debug")
def debug_progress(kid_id: int, session: Session = Depends(get_session)):
    """Detailed progress breakdown for debugging."""
    from datetime import timedelta
    from sqlalchemy.orm import selectinload
    from ..models import Settings, PayoutMode
    from ..services.rotation import RotationService

    kid = session.get(User, kid_id)
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")

    today = date.today()
    week_id = today.strftime("%G-W%V")
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # Active chores
    stmt = select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)
    chores = session.exec(stmt).all()

    chore_details = []
    for c in chores:
        if c.frequency == "DAILY":
            days = 5 if c.weekdays_only else 7
        else:
            days = 1
        chore_details.append({
            "id": c.id, "name": c.name, "frequency": c.frequency,
            "weekdays_only": c.weekdays_only, "due_day": c.due_day,
            "reward": c.reward, "expected_instances": days,
        })

    # Week logs
    stmt = select(ChoreLog).where(
        ChoreLog.kid_id == kid_id,
        ChoreLog.date >= monday,
        ChoreLog.date <= sunday,
    ).options(selectinload(ChoreLog.chore))
    logs = session.exec(stmt).all()

    log_details = []
    for l in logs:
        log_details.append({
            "id": l.id, "chore_id": l.chore_id,
            "chore_name": l.chore.name if l.chore else "?",
            "date": l.date.isoformat(), "status": l.status,
            "week_id": l.week_id,
        })

    # Rotation
    rotation_svc = RotationService(session)
    rotation_expected = rotation_svc.calculate_expected_instances(kid_id, week_id)
    rotation_completed = rotation_svc.count_completed_instances(kid_id, week_id)
    rotation_today = rotation_svc.get_todays_rotation_chores(kid_id, today)

    # Totals
    total_expected = sum(c["expected_instances"] for c in chore_details) + rotation_expected
    total_approved = sum(1 for l in logs if l.status == ChoreStatus.APPROVED) + rotation_completed
    total_pending = sum(1 for l in logs if l.status == ChoreStatus.PENDING)
    total_completed_reward = sum((l.chore.reward if l.chore else 0) for l in logs if l.status in (ChoreStatus.APPROVED, ChoreStatus.PENDING))
    total_possible_reward = sum(c["expected_instances"] * c["reward"] for c in chore_details)

    mode_setting = session.get(Settings, "payout_mode")
    payout_mode = mode_setting.value if mode_setting else PayoutMode.ALL_OR_NOTHING
    threshold_setting = session.get(Settings, "payout_threshold")
    threshold_pct = int(threshold_setting.value) if threshold_setting else 80

    raw_pct = int((total_approved / total_expected) * 100) if total_expected > 0 else 0

    return {
        "kid": kid.name,
        "today": today.isoformat(),
        "week_id": week_id,
        "monday": monday.isoformat(),
        "sunday": sunday.isoformat(),
        "payout_mode": payout_mode,
        "threshold_pct": threshold_pct,
        "chores": chore_details,
        "logs_this_week": log_details,
        "rotation_expected_week": rotation_expected,
        "rotation_completed_week": rotation_completed,
        "rotation_today": rotation_today,
        "totals": {
            "expected_instances": total_expected,
            "approved_instances": total_approved,
            "pending_instances": total_pending,
            "raw_week_pct": raw_pct,
            "completed_reward": round(total_completed_reward, 2),
            "total_possible_reward": round(total_possible_reward, 2),
        }
    }

@router.get("/{kid_id}/rotation-chores")
def get_kid_rotation_chores(kid_id: int, session: Session = Depends(get_session)):
    """Get rotation chores assigned to this kid for today."""
    from ..services.rotation import RotationService
    svc = RotationService(session)
    return svc.get_todays_rotation_chores(kid_id)

@router.get("/{kid_id}/chores")
def get_kid_chores(
    kid_id: int, 
    date_str: Optional[str] = Query(None, alias="date"), 
    session: Session = Depends(get_session)
):
    target_date = date.today()
    # Basic date parsing
    if date_str:
        from datetime import date as dt_date
        target_date = dt_date.fromisoformat(date_str)
    
    # 1. Get Assigned Chores
    stmt = select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)
    chores = session.exec(stmt).all()
    
    # 2. Get Logs for today
    service = ChoreService(session)
    logs = service.get_today_logs(kid_id, target_date)
    log_map = {log.chore_id: log for log in logs}
    
    # 3. Merge — only include chores that are due today
    result = []
    weekday = target_date.weekday()  # 0=Monday, 6=Sunday
    
    for chore in chores:
        # Skip weekly chores that aren't due today
        if chore.frequency == "WEEKLY":
            if chore.due_day is not None and chore.due_day != weekday:
                continue
        
        # Skip weekdays-only chores on weekends (Saturday=5, Sunday=6)
        if chore.weekdays_only and weekday >= 5:
            continue
        
        log = log_map.get(chore.id)
        status = log.status if log else ChoreStatus.INCOMPLETE
        result.append({
            "id": chore.id,
            "name": chore.name,
            "reward": chore.reward,
            "status": status,
            "description": chore.description,
            "frequency": chore.frequency,
            "due_day": chore.due_day,
            "weekdays_only": chore.weekdays_only,
            "icon": "default"
        })
        
    return result
