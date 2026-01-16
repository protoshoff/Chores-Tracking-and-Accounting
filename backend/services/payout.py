from typing import List
from datetime import date, datetime
from sqlmodel import Session, select
from ..models import User, Chore, ChoreLog, ChoreStatus, WeeklyRollup, TransactionType
from ..services.ledger import LedgerService

class PayoutService:
    def __init__(self, session: Session):
        self.session = session
        self.ledger = LedgerService(session)

    def calculate_and_payout(self, kid_id: int, week_id: str):
        # 1. Get Rollup to avoid double payout
        stmt = select(WeeklyRollup).where(WeeklyRollup.kid_id == kid_id, WeeklyRollup.week_id == week_id)
        existing = self.session.exec(stmt).first()
        if existing:
            return existing

        # 2. Get Kid
        kid = self.session.get(User, kid_id)
        if not kid:
            raise ValueError("Kid not found")
            
        # 3. Calculate Weights
        # Get all chore logs for this week
        stmt = select(ChoreLog).where(ChoreLog.kid_id == kid_id, ChoreLog.week_id == week_id)
        logs = self.session.exec(stmt).all()
        
        # We need also the 'Possible' weight. This is tricky because chores might change.
        # For v0.1: We sum the weight of all logs. If log exists, it was expected?
        # WAIT: Logs are created on demand. We need to know what was EXPECTED.
        # Simplified Logic (v0.1): 
        # - Iterate all ACTIVE chores assigned to kid. 
        # - Check frequency. If DAILY, expect 7 instances. If WEEKLY, expect 1.
        # - Sum up total expected weight.
        # - Sum up total APPROVED weight from logs.
        
        total_possible = 0
        total_completed = 0
        
        # Get Active Chores
        chores = self.session.exec(select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)).all()
        
        for chore in chores:
            instances = 7 if chore.frequency == "DAILY" else 1
            chore_weight = chore.weight * instances
            total_possible += chore_weight
            
        # Get Approved Logs
        approved_weight = 0
        for log in logs:
            if log.status == ChoreStatus.APPROVED:
                # We need the chore weight. 
                # Ideally ChoreLog snapshots weight, but for now we join or lazy load
                # Assuming weight hasn't changed drastically mid-week.
                if log.chore:
                    approved_weight += log.chore.weight

        total_completed = approved_weight
        
        # 4. Calculate Payout (Prorated)
        payout_cents = 0
        if total_possible > 0:
            ratio = min(1.0, total_completed / total_possible)
            payout_cents = int(kid.allowance_cents * ratio)
            
        # 5. Execute Payout
        if payout_cents > 0:
            self.ledger.add_transaction(
                kid_id=kid_id,
                amount_cents=payout_cents,
                transaction_type=TransactionType.ALLOWANCE,
                description=f"Weekly Allowance ({week_id})",
                week_id=week_id
            )
            
        # 6. Save Rollup
        rollup = WeeklyRollup(
            kid_id=kid_id,
            week_id=week_id,
            total_weight_possible=total_possible,
            total_weight_completed=total_completed,
            payout_cents=payout_cents,
            finalized_at=datetime.utcnow()
        )
        self.session.add(rollup)
        self.session.commit()
        return rollup
