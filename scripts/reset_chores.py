from sqlmodel import Session, select
from backend.db import engine
from backend.models import ChoreLog, ChoreStatus

def reset_chores():
    with Session(engine) as session:
        logs = session.exec(select(ChoreLog)).all()
        count = 0
        for log in logs:
            if log.status != ChoreStatus.INCOMPLETE:
                log.status = ChoreStatus.INCOMPLETE
                log.completed_at = None
                log.reviewed_at = None
                session.add(log)
                count += 1
        session.commit()
        print(f"Reset {count} chores to INCOMPLETE.")

if __name__ == "__main__":
    reset_chores()
