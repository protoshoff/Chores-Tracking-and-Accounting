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
            
        # 3. Count Instances (Instance-Based Calculation)
        # Get all chore logs for this week
        stmt = select(ChoreLog).where(ChoreLog.kid_id == kid_id, ChoreLog.week_id == week_id)
        logs = self.session.exec(stmt).all()
        
        # Calculate total expected instances and completed instances
        # - DAILY chores: 7 instances per week
        # - WEEKLY chores: 1 instance per week
        
        total_expected_instances = 0
        completed_instances = 0
        
        # Get Active Chores to calculate expected instances
        chores = self.session.exec(select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)).all()
        
        for chore in chores:
            instances = 7 if chore.frequency == "DAILY" else 1
            total_expected_instances += instances
            
        # Count approved logs (completed instances)
        for log in logs:
            if log.status == ChoreStatus.APPROVED:
                completed_instances += 1

        # Calculate legacy reward values for rollup record
        total_possible = 0.0
        total_completed = 0.0
        for chore in chores:
            instances = 7 if chore.frequency == "DAILY" else 1
            total_possible += chore.reward * instances
        for log in logs:
            if log.status == ChoreStatus.APPROVED and log.chore:
                total_completed += log.chore.reward
        
        # 4. Calculate Payout (Mode-Based)
        from ..models import Settings, PayoutMode
        
        # Fetch payout mode (default: ALL_OR_NOTHING)
        mode_setting = self.session.get(Settings, "payout_mode")
        payout_mode = mode_setting.value if mode_setting else PayoutMode.ALL_OR_NOTHING
        
        # Fetch threshold (default: 80%)
        threshold_setting = self.session.get(Settings, "payout_threshold")
        threshold_pct = int(threshold_setting.value) if threshold_setting else 80

        payout = 0.0
        if total_expected_instances > 0:
            # Calculate completion percentage based on instance count
            completion_pct = (completed_instances / total_expected_instances) * 100
            
            if payout_mode == PayoutMode.ALL_OR_NOTHING:
                # All-or-Nothing: Full allowance if >= threshold, else $0
                if completion_pct >= threshold_pct:
                    payout = round(kid.allowance, 2)
                else:
                    payout = 0.0
            else:  # PayoutMode.PRORATED
                # Proportional: Pay based on completion percentage
                payout = round((completed_instances / total_expected_instances) * kid.allowance, 2)
                # Safety check: don't exceed allowance
                payout = min(payout, kid.allowance)
            
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
