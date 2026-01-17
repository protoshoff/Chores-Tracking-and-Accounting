from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from datetime import datetime, timedelta, date
from ..db import engine
from ..models import Chore, ChoreLog, ChoreStatus, User
from .payout import PayoutService
import logging

logger = logging.getLogger("chores.automation")

class AutomationService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        # Daily Maintenance at 00:01
        self.scheduler.add_job(
            self.daily_maintenance, 
            CronTrigger(hour=0, minute=1),
            id="daily_maintenance",
            replace_existing=True
        )
        
        # Weekly Tally at Sunday 00:05
        # (Give daily maintenance a moment to finish)
        self.scheduler.add_job(
            self.weekly_tally,
            CronTrigger(day_of_week='sun', hour=0, minute=5),
            id="weekly_tally",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Automation Scheduler Started")

    async def daily_maintenance(self):
        """Mark yesterday's uncompleted daily chores as INCOMPLETE/MISSED"""
        logger.info("Running Daily Maintenance...")
        with Session(engine) as session:
            yesterday = date.today() - timedelta(days=1)
            week_id = yesterday.strftime("%Y-W%W")
            
            # Find all active Daily chores
            chores = session.exec(select(Chore).where(Chore.frequency == "DAILY", Chore.archived == False)).all()
            
            for chore in chores:
                # Check if log exists for yesterday
                stmt = select(ChoreLog).where(
                    ChoreLog.chore_id == chore.id,
                    ChoreLog.date == yesterday
                )
                log = session.exec(stmt).first()
                
                if not log:
                    # No attempt made -> Create Incomplete Log (Missed)
                    missed_log = ChoreLog(
                        chore_id=chore.id,
                        kid_id=chore.kid_id,
                        week_id=week_id,
                        date=yesterday,
                        status=ChoreStatus.INCOMPLETE,
                        notes="System: Auto-marked missed"
                    )
                    session.add(missed_log)
                elif log.status == ChoreStatus.PENDING:
                     # Optional: Auto-reject pending if not reviewed? 
                     # For now, we leave pending as is (grace period), or maybe specific rule.
                     # Spec says: "Missed chores automatically marked when due window closes."
                     # Usually means if it wasn't done. If it's pending, it WAS done, just not approved.
                     pass
            
            session.commit()
        logger.info("Daily Maintenance Complete.")

    async def weekly_tally(self):
        """Calculate Payouts for all kids for the PREVIOUS week"""
        logger.info("Running Weekly Tally...")
        with Session(engine) as session:
            payout_svc = PayoutService(session)
            
            # Identify "Last Week" (The week that just ended yesterday, Saturday)
            # Since this runs Sunday morning, "Today" is start of new week.
            # "Yesterday" was end of previous week.
            yesterday = date.today() - timedelta(days=1)
            week_id = yesterday.strftime("%Y-W%W")
            
            kids = session.exec(select(User).where(User.is_active == True)).all()
            
            for kid in kids:
                try:
                    logger.info(f"Calculating tally for {kid.name} ({week_id})")
                    payout_svc.calculate_and_payout(kid.id, week_id)
                except Exception as e:
                    logger.error(f"Error tallying for {kid.name}: {e}")
            
        logger.info("Weekly Tally Complete.")
