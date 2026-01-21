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
        # - Sum up total expected reward.
        # - Sum up total APPROVED reward from logs.
        
        total_possible = 0.0
        total_completed = 0.0
        
        # Get Active Chores
        chores = self.session.exec(select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)).all()
        
        for chore in chores:
            instances = 7 if chore.frequency == "DAILY" else 1
            chore_total = chore.reward * instances
            total_possible += chore_total
            
        # Get Approved Logs
        approved_reward = 0.0
        for log in logs:
            if log.status == ChoreStatus.APPROVED:
                # We need the chore reward. 
                # Ideally ChoreLog snapshots reward, but for now we join or lazy load
                # Assuming reward hasn't changed drastically mid-week.
                if log.chore:
                    approved_reward += log.chore.reward

        total_completed = approved_reward
        
        # 4. Calculate Payout (Prorated)
        payout = 0.0
        if total_possible > 0:
            ratio = min(1.0, total_completed / total_possible)
            payout = round(kid.allowance * ratio, 2)
            
        # 5. Execute Payout
        if payout > 0:
            self.ledger.add_transaction(
                kid_id=kid_id,
                amount=payout,
                transaction_type=TransactionType.ALLOWANCE,
                description=f"Weekly Allowance ({week_id})",
                week_id=week_id
            )
            
        # 6. Save Rollup
        rollup = WeeklyRollup(
            kid_id=kid_id,
            week_id=week_id,
            total_reward_possible=total_possible,
            total_reward_completed=total_completed,
            payout=payout,
            finalized_at=datetime.utcnow()
        )
        self.session.add(rollup)
        self.session.commit()
        return rollup
