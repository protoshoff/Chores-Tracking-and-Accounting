from datetime import date, datetime
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
        
        week_id = target_date.strftime("%Y-W%W")

        if existing:
            # Update existing
            existing.status = ChoreStatus.PENDING
            existing.completed_at = datetime.utcnow()
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
                completed_at=datetime.utcnow()
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
                
        if total_possible == 0:
            return {
                "total_reward": 0.0,
                "completed_reward": 0.0,
                "approved_reward": 0.0,
                "pending_count": 0,
                "today_done": 0,
                "today_total": 0,
                "week_pct": 0
            }

        # 2. Get Week's Logs
        today = date.today()
        week_id = today.strftime("%Y-W%W")
        
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
        
        return {
            "total_reward": round(total_possible, 2),
            "completed_reward": round(completed_reward, 2),
            "approved_reward": round(approved_reward, 2),
            "pending_count": pending_count,
            "today_done": today_done,
            "today_total": daily_chores_count,
            "week_pct": int((approved_reward / total_possible) * 100)
        }
