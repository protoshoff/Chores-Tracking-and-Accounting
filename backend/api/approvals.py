from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timezone
from ..db import get_session
from ..models import ChoreLog, ChoreStatus, User, Chore

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

from pydantic import BaseModel

class PendingChore(BaseModel):
    id: int
    kid_id: int
    kid_name: str
    chore_id: int
    chore_name: str
    date: str
    status: str
    completed_at: datetime | None
    reward: float = 0.0
    is_rotation: bool = False

@router.get("/pending", response_model=List[PendingChore])
def get_pending_approvals(session: Session = Depends(get_session)):
    # Join upfront to avoid N+1 lazy loads
    stmt = (
        select(ChoreLog, User, Chore)
        .join(User, ChoreLog.kid_id == User.id)
        .join(Chore, ChoreLog.chore_id == Chore.id)
        .where(ChoreLog.status == ChoreStatus.PENDING)
        .order_by(ChoreLog.completed_at)
    )
    results = session.exec(stmt).all()

    pending = [
        PendingChore(
            id=log.id,
            kid_id=log.kid_id,
            kid_name=kid.name,
            chore_id=log.chore_id,
            chore_name=chore.name,
            date=log.date.isoformat(),
            status=log.status,
            completed_at=log.completed_at,
            reward=chore.reward,
        )
        for log, kid, chore in results
    ]

    # Also include pending rotation chores
    from ..services.rotation import RotationService
    rotation_svc = RotationService(session)
    for r in rotation_svc.get_pending_approvals():
        pending.append(PendingChore(
            id=r["id"],
            kid_id=r["kid_id"],
            kid_name=r["kid_name"],
            chore_id=r["group_id"],  # Using group_id in chore_id field
            chore_name=r["chore_name"],
            date=r["date"],
            status=r["status"],
            completed_at=r["completed_at"],
            reward=r["reward"],
            is_rotation=True,
        ))

    return pending

class ReviewRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"

from ..services.stats import StreakService

@router.post("/{log_id}/review")
def review_chore(
    log_id: int, 
    action: ReviewRequest,
    is_rotation: bool = False,
    session: Session = Depends(get_session)
):
    # Route rotation reviews to the rotation endpoint
    if is_rotation:
        from .rotations import review_rotation_log, ReviewRequest as RotReview
        return review_rotation_log(log_id, RotReview(action=action.action), session)

    log = session.get(ChoreLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    act = action.action
    if act == "APPROVE":
        log.status = ChoreStatus.APPROVED
    elif act == "REJECT":
        log.status = ChoreStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    log.reviewed_at = datetime.now(timezone.utc)
    session.add(log)
    session.commit()
    session.refresh(log)
    
    # Update Streak if approved
    if log.status == ChoreStatus.APPROVED:
        StreakService(session).update_streak(log.kid_id)
        
        # Check if this approval is for a past week that already has a rollup.
        # If so, re-run the payout to credit the retroactive approval.
        try:
            _handle_retroactive_payout(log, session)
        except Exception as e:
            import logging
            logging.getLogger("chores.approvals").error(f"Retroactive payout failed: {e}")
        
    return log


def _handle_retroactive_payout(log: ChoreLog, session: Session):
    """If a chore is approved after its week's payout already ran, issue a catch-up credit."""
    from ..models import WeeklyRollup, TransactionType, Settings, PayoutMode
    from ..services.ledger import LedgerService
    
    week_id = log.week_id
    kid_id = log.kid_id
    
    # Check if a rollup already exists for this week
    stmt = select(WeeklyRollup).where(
        WeeklyRollup.kid_id == kid_id,
        WeeklyRollup.week_id == week_id,
    )
    existing_rollup = session.exec(stmt).first()
    
    if not existing_rollup:
        # No rollup yet — normal flow, weekly tally will handle it
        return
    
    # Re-calculate what the payout SHOULD be now with this newly approved chore
    from ..models import Chore as ChoreModel, Frequency
    
    kid = session.get(User, kid_id)
    if not kid:
        return
    
    # Count all approved logs for this week (including the one just approved)
    all_logs = session.exec(
        select(ChoreLog).where(ChoreLog.kid_id == kid_id, ChoreLog.week_id == week_id)
    ).all()
    completed_instances = sum(1 for l in all_logs if l.status == ChoreStatus.APPROVED)
    
    # Count expected instances
    chores = session.exec(
        select(ChoreModel).where(ChoreModel.kid_id == kid_id, ChoreModel.archived == False)
    ).all()
    total_expected = sum(7 if c.frequency == Frequency.DAILY else 1 for c in chores)
    
    if total_expected == 0:
        return
    
    # Get payout settings
    mode_setting = session.get(Settings, "payout_mode")
    payout_mode = mode_setting.value if mode_setting else PayoutMode.ALL_OR_NOTHING
    threshold_setting = session.get(Settings, "payout_threshold")
    threshold_pct = int(threshold_setting.value) if threshold_setting else 80
    
    # Calculate what payout should be now
    completion_pct = (completed_instances / total_expected) * 100
    
    if payout_mode == PayoutMode.ALL_OR_NOTHING:
        new_payout = round(kid.allowance, 2) if completion_pct >= threshold_pct else 0.0
    else:  # PRORATED
        new_payout = round((completed_instances / total_expected) * kid.allowance, 2)
        new_payout = min(new_payout, kid.allowance)
    
    # Credit the difference
    diff = round(new_payout - existing_rollup.payout, 2)
    
    if diff > 0:
        ledger = LedgerService(session)
        ledger.add_transaction(
            kid_id=kid_id,
            amount=diff,
            transaction_type=TransactionType.ALLOWANCE,
            description=f"Retroactive approval catch-up ({week_id})",
            week_id=week_id,
        )
        
        # Update the rollup record
        existing_rollup.payout = new_payout
        session.add(existing_rollup)
        session.commit()
        
        import logging
        logging.getLogger("chores.approvals").info(
            f"Retroactive approval: {kid.name} week {week_id} — "
            f"catch-up credit ${diff:.2f} (${existing_rollup.payout - diff:.2f} → ${new_payout:.2f})"
        )
