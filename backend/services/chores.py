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
