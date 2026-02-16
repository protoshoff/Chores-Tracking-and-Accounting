"""API endpoints for rotation (alternating/shared) chores."""
from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from ..db import get_session
from ..models import (
    RotationGroup, RotationMember, RotationLog, RotationFrequency,
    ChoreStatus, User
)
from ..services.rotation import RotationService

router = APIRouter(prefix="/api/rotations", tags=["Rotations"])


# --- Request Models ---

class RotationMemberIn(BaseModel):
    kid_id: int
    position: int


class RotationGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    frequency: RotationFrequency
    start_date: str  # "YYYY-MM-DD"
    members: List[RotationMemberIn]


class RotationGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[RotationFrequency] = None
    start_date: Optional[str] = None
    members: Optional[List[RotationMemberIn]] = None
    archived: Optional[bool] = None


class ReviewRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"


# --- Endpoints ---

@router.get("/")
def list_rotation_groups(archived: bool = False, session: Session = Depends(get_session)):
    stmt = select(RotationGroup)
    if not archived:
        stmt = stmt.where(RotationGroup.archived == False)
    groups = session.exec(stmt).all()

    result = []
    for group in groups:
        members = session.exec(
            select(RotationMember)
            .where(RotationMember.group_id == group.id)
            .order_by(RotationMember.position)
        ).all()

        result.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "frequency": group.frequency,
            "start_date": group.start_date.isoformat(),
            "archived": group.archived,
            "members": [
                {
                    "id": m.id,
                    "kid_id": m.kid_id,
                    "kid_name": m.kid.name if m.kid else "Unknown",
                    "position": m.position,
                }
                for m in members
            ],
        })
    return result


@router.post("/", status_code=201)
def create_rotation_group(payload: RotationGroupCreate, session: Session = Depends(get_session)):
    if len(payload.members) < 1:
        raise HTTPException(status_code=400, detail="At least 1 member required")

    # Validate members exist
    for m in payload.members:
        kid = session.get(User, m.kid_id)
        if not kid:
            raise HTTPException(status_code=404, detail=f"Kid {m.kid_id} not found")

    try:
        start = date.fromisoformat(payload.start_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid start_date format (YYYY-MM-DD)")

    group = RotationGroup(
        name=payload.name,
        description=payload.description,
        frequency=payload.frequency,
        start_date=start,
        archived=False,
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    for m in payload.members:
        member = RotationMember(
            group_id=group.id,
            kid_id=m.kid_id,
            position=m.position,
        )
        session.add(member)
    session.commit()

    return {"id": group.id, "status": "created"}


@router.put("/{group_id}")
def update_rotation_group(group_id: int, payload: RotationGroupUpdate, session: Session = Depends(get_session)):
    group = session.get(RotationGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Rotation group not found")

    if payload.name is not None:
        group.name = payload.name
    if payload.description is not None:
        group.description = payload.description
    if payload.frequency is not None:
        group.frequency = payload.frequency
    if payload.start_date is not None:
        try:
            group.start_date = date.fromisoformat(payload.start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date")
    if payload.archived is not None:
        group.archived = payload.archived

    session.add(group)

    # Replace members if provided
    if payload.members is not None:
        # Delete old members
        old_members = session.exec(
            select(RotationMember).where(RotationMember.group_id == group_id)
        ).all()
        for m in old_members:
            session.delete(m)

        for m in payload.members:
            member = RotationMember(
                group_id=group_id,
                kid_id=m.kid_id,
                position=m.position,
            )
            session.add(member)

    session.commit()
    return {"status": "updated"}


@router.delete("/{group_id}")
def archive_rotation_group(group_id: int, session: Session = Depends(get_session)):
    group = session.get(RotationGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Rotation group not found")
    group.archived = True
    session.add(group)
    session.commit()
    return {"status": "archived", "id": group_id}


@router.get("/{group_id}/schedule")
def get_schedule(group_id: int, weeks: int = 2, session: Session = Depends(get_session)):
    svc = RotationService(session)
    return svc.get_schedule(group_id, weeks)


@router.post("/{group_id}/complete")
def complete_rotation_chore(
    group_id: int,
    payload: dict = None,
    session: Session = Depends(get_session),
):
    """Mark today's rotation chore as complete. Payload: {kid_id: int, date?: "YYYY-MM-DD"}"""
    if not payload or "kid_id" not in payload:
        raise HTTPException(status_code=400, detail="kid_id required")

    kid_id = payload["kid_id"]
    target_date = date.today()
    if "date" in payload and payload["date"]:
        try:
            target_date = date.fromisoformat(payload["date"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    # Verify this kid is actually assigned today
    svc = RotationService(session)
    group = session.get(RotationGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Rotation group not found")

    assigned = svc.get_assigned_kid(group, target_date)
    if assigned != kid_id:
        raise HTTPException(status_code=400, detail="This kid is not assigned to this chore today")

    log = svc.mark_complete(group_id, kid_id, target_date)
    return {"status": log.status, "message": "Marked complete", "log_id": log.id}


@router.post("/log/{log_id}/review")
def review_rotation_log(log_id: int, action: ReviewRequest, session: Session = Depends(get_session)):
    """Approve or reject a rotation chore log."""
    log = session.get(RotationLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    if action.action == "APPROVE":
        log.status = ChoreStatus.APPROVED
    elif action.action == "REJECT":
        log.status = ChoreStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    log.reviewed_at = datetime.now(timezone.utc)
    session.add(log)
    session.commit()

    # Handle retroactive payout (same logic as regular chores)
    if log.status == ChoreStatus.APPROVED:
        _handle_retroactive_rotation_payout(log, session)

    return {"status": "success", "action": action.action}


def _handle_retroactive_rotation_payout(log: RotationLog, session: Session):
    """Same concept as approvals._handle_retroactive_payout but for rotation logs."""
    from ..models import WeeklyRollup, Settings, PayoutMode, Chore, Frequency
    from ..services.ledger import LedgerService

    week_id = log.week_id
    kid_id = log.kid_id

    stmt = select(WeeklyRollup).where(
        WeeklyRollup.kid_id == kid_id,
        WeeklyRollup.week_id == week_id,
    )
    existing_rollup = session.exec(stmt).first()
    if not existing_rollup:
        return  # No rollup yet — weekly tally will handle it

    # Recalculate what payout should be now
    kid = session.get(User, kid_id)
    if not kid:
        return

    # Regular chore instances
    from ..models import ChoreLog as CL
    regular_chores = session.exec(
        select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)
    ).all()
    total_expected = sum(7 if c.frequency == Frequency.DAILY else 1 for c in regular_chores)

    regular_logs = session.exec(
        select(CL).where(CL.kid_id == kid_id, CL.week_id == week_id)
    ).all()
    completed = sum(1 for l in regular_logs if l.status == ChoreStatus.APPROVED)

    # Rotation instances
    rotation_svc = RotationService(session)
    total_expected += rotation_svc.calculate_expected_instances(kid_id, week_id)
    completed += rotation_svc.count_completed_instances(kid_id, week_id)

    if total_expected == 0:
        return

    # Get payout settings
    mode_setting = session.get(Settings, "payout_mode")
    payout_mode = mode_setting.value if mode_setting else PayoutMode.ALL_OR_NOTHING
    threshold_setting = session.get(Settings, "payout_threshold")
    threshold_pct = int(threshold_setting.value) if threshold_setting else 80

    completion_pct = (completed / total_expected) * 100

    if payout_mode == PayoutMode.ALL_OR_NOTHING:
        new_payout = round(kid.allowance, 2) if completion_pct >= threshold_pct else 0.0
    else:
        new_payout = round((completed / total_expected) * kid.allowance, 2)
        new_payout = min(new_payout, kid.allowance)

    diff = round(new_payout - existing_rollup.payout, 2)
    if diff > 0:
        ledger = LedgerService(session)
        from ..models import TransactionType
        ledger.add_transaction(
            kid_id=kid_id,
            amount=diff,
            transaction_type=TransactionType.ALLOWANCE,
            description=f"Retroactive rotation approval catch-up ({week_id})",
            week_id=week_id,
        )
        existing_rollup.payout = new_payout
        session.add(existing_rollup)
        session.commit()
