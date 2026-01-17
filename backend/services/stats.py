from datetime import date, timedelta
from typing import List
from sqlmodel import Session, select
from ..models import ChoreLog, ChoreStatus, Streak

class StreakService:
    def __init__(self, session: Session):
        self.session = session

    def update_streak(self, kid_id: int):
        """Recalculate and save streak for a kid."""
        # 1. Get all approved logs dates
        stmt = select(ChoreLog.date).where(
            ChoreLog.kid_id == kid_id,
            ChoreLog.status == ChoreStatus.APPROVED
        ).distinct()
        results = self.session.exec(stmt).all()
        # Convert to set of strings or dates for fast lookup
        approved_dates = set(results) # results are 'date' objects
        
        today = date.today()
        current_streak = 0
        
        # Check Today
        if today in approved_dates:
            current_streak += 1
            check_date = today - timedelta(days=1)
        else:
            # If today not done, start checking yesterday
            check_date = today - timedelta(days=1)
            
        # Loop backwards
        while check_date in approved_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
            
        # Update DB
        streak_record = self.session.get(Streak, kid_id)
        if not streak_record:
            streak_record = Streak(kid_id=kid_id)
            
        streak_record.current_streak_days = current_streak
        # Update max streak?
        if current_streak > streak_record.max_streak_days:
            streak_record.max_streak_days = current_streak
            
        # last_completed_date is the date of the most recent approved chore
        # If 'today' in approved_dates, it's today. Else if 'yesterday', etc.
        # Simple query for max date
        stmt_max = select(ChoreLog.date).where(
             ChoreLog.kid_id == kid_id,
             ChoreLog.status == ChoreStatus.APPROVED
        ).order_by(ChoreLog.date.desc()).limit(1)
        last_date = self.session.exec(stmt_max).first()
        streak_record.last_completed_date = last_date
        
        self.session.add(streak_record)
        self.session.commit()
        return streak_record
