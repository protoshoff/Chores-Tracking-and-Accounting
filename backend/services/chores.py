from datetime import date, datetime, timezone
from typing import Optional, List
from sqlmodel import Session, select
from ..models import Chore, ChoreLog, ChoreStatus, User

class ChoreService:
    def __init__(self, session: Session):
        self.session = session

    def get_today_logs(self, kid_id: int, target_date: date) -> List[ChoreLog]:
        stmt = select(ChoreLog).where(
            ChoreLog.kid_id == kid_id,
            ChoreLog.date == target_date
        )
        return self.session.exec(stmt).all()

    def mark_complete(self, chore_id: int, kid_id: int, target_date: date) -> ChoreLog:
        # Check if log exists
        stmt = select(ChoreLog).where(
            ChoreLog.chore_id == chore_id,
            ChoreLog.kid_id == kid_id,
            ChoreLog.date == target_date
        )
        existing = self.session.exec(stmt).first()
        
        week_id = target_date.strftime("%G-W%V")

        if existing:
            # Update existing
            existing.status = ChoreStatus.PENDING
            existing.completed_at = datetime.now(timezone.utc)
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            # Create new log
            new_log = ChoreLog(
                chore_id=chore_id,
                kid_id=kid_id,
                date=target_date,
                week_id=week_id,
                status=ChoreStatus.PENDING,
                completed_at=datetime.now(timezone.utc)
            )
            self.session.add(new_log)
            self.session.commit()
            self.session.refresh(new_log)
            return new_log

    def calculate_weekly_progress(self, kid_id: int):
        # 1. Calculate Total Possible Reward
        # Get active chores
        stmt = select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)
        chores = self.session.exec(stmt).all()
        
        total_possible = 0.0
        for chore in chores:
            if chore.frequency == "DAILY":
                total_possible += chore.reward * 7
            else:
                total_possible += chore.reward

        # 2. Get Week's Logs
        today = date.today()
        week_id = today.strftime("%G-W%V")
        
        # Eager load chore to prevent N+1 and potential locks
        from sqlalchemy.orm import selectinload
        stmt = select(ChoreLog).where(
            ChoreLog.kid_id == kid_id,
            ChoreLog.week_id == week_id
        ).options(selectinload(ChoreLog.chore))
        
        logs = self.session.exec(stmt).all()
        
        completed_reward = 0.0
        approved_reward = 0.0
        pending_count = 0
        
        for log in logs:
            # Safe access
            reward = log.chore.reward if log.chore else 0.0
            
            if log.status in (ChoreStatus.APPROVED, ChoreStatus.PENDING, "COMPLETED"):
                completed_reward += reward
            
            if log.status == ChoreStatus.APPROVED:
                approved_reward += reward
                
            if log.status == ChoreStatus.PENDING:
                pending_count += 1
                
        # 3. Today Stats
        today_logs = [l for l in logs if l.date == today]
        today_done = len([l for l in today_logs if l.status != ChoreStatus.INCOMPLETE])
        
        # Today Total is active daily chores + any weekly chores due today
        daily_chores_count = 0
        weekday = today.weekday()
        
        for c in chores:
            if c.frequency == "DAILY":
                daily_chores_count += 1
            elif c.frequency == "WEEKLY" and c.due_day is not None:
                if c.due_day == weekday:
                    daily_chores_count += 1
        
        # Calculate week_pct based on payout mode
        from ..models import Settings, PayoutMode
        
        mode_setting = self.session.get(Settings, "payout_mode")
        payout_mode = mode_setting.value if mode_setting else PayoutMode.ALL_OR_NOTHING
        
        # Calculate raw completion percentage
        raw_week_pct = int((approved_reward / total_possible) * 100) if total_possible > 0 else 0
        
        # Get threshold setting (used by ALL_OR_NOTHING mode)
        threshold_setting = self.session.get(Settings, "payout_threshold")
        threshold_pct = int(threshold_setting.value) if threshold_setting else 80
        
        # Apply payout mode logic
        if payout_mode == PayoutMode.ALL_OR_NOTHING:
            week_pct = 100 if raw_week_pct >= threshold_pct else raw_week_pct
        else:
            week_pct = raw_week_pct
        
        # Include rotation chores in today stats
        rotation_today_total = 0
        rotation_today_done = 0
        rotation_expected_week = 0
        rotation_completed_week = 0
        try:
            from .rotation import RotationService
            rotation_svc = RotationService(self.session)
            rotation_today = rotation_svc.get_todays_rotation_chores(kid_id, today)
            rotation_today_total = len(rotation_today)
            rotation_today_done = sum(1 for r in rotation_today if r["status"] != ChoreStatus.INCOMPLETE)
            
            # Include rotation in week percentage
            rotation_expected_week = rotation_svc.calculate_expected_instances(kid_id, week_id)
            rotation_completed_week = rotation_svc.count_completed_instances(kid_id, week_id)
        except Exception as e:
            print(f"Warning: rotation stats failed for kid {kid_id}: {e}")
        
        # Recalculate week_pct including rotations
        total_week_expected = sum(
            7 if c.frequency == "DAILY" else 1 for c in chores
        ) + rotation_expected_week
        total_week_completed = sum(
            1 for l in logs if l.status == ChoreStatus.APPROVED
        ) + rotation_completed_week
        
        if total_week_expected > 0:
            raw_week_pct = int((total_week_completed / total_week_expected) * 100)
            if payout_mode == PayoutMode.ALL_OR_NOTHING:
                week_pct = 100 if raw_week_pct >= threshold_pct else raw_week_pct
            else:
                week_pct = raw_week_pct
        
        return {
            "total_reward": round(total_possible, 2),
            "completed_reward": round(completed_reward, 2),
            "approved_reward": round(approved_reward, 2),
            "pending_count": pending_count,
            "today_done": today_done + rotation_today_done,
            "today_total": daily_chores_count + rotation_today_total,
            "week_pct": week_pct
        }
