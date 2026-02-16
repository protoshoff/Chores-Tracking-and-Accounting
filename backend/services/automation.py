from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from datetime import datetime, timedelta, date
from ..db import engine
from ..models import Chore, ChoreLog, ChoreStatus, User
from .payout import PayoutService
import logging

logger = logging.getLogger("chores.automation")

# Global instance for accessing from API
_automation_instance = None

def get_automation_service():
    """Get the global automation service instance"""
    return _automation_instance

class AutomationService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def start(self):
        global _automation_instance
        _automation_instance = self  # Store instance for API access
        
        # Check for missed weekly payouts on startup
        await self.check_missed_payouts()
        
        # Daily Maintenance at 00:01
        self.scheduler.add_job(
            self.daily_maintenance, 
            CronTrigger(hour=0, minute=1),
            id="daily_maintenance",
            replace_existing=True
        )
        
        # Weekly Tally - Read schedule from settings
        self.schedule_weekly_tally()
        
        self.scheduler.start()
        logger.info("Automation Scheduler Started")
    
    def schedule_weekly_tally(self):
        """Schedule weekly tally job using settings from database (timezone-aware)"""
        from ..models import Settings
        import os
        import time as time_module
        
        with Session(engine) as session:
            # Read timezone from settings
            tz_setting = session.get(Settings, "timezone")
            configured_tz = tz_setting.value if tz_setting else None
            
            # Read schedule from settings  
            day_setting = session.get(Settings, "payout_day")
            hour_setting = session.get(Settings, "payout_hour")
            minute_setting = session.get(Settings, "payout_minute")
            
            # Defaults: Sunday at 00:05
            payout_day = int(day_setting.value) if day_setting else 6  # 6 = Sunday
            payout_hour = int(hour_setting.value) if hour_setting else 0
            payout_minute = int(minute_setting.value) if minute_setting else 5
        
        # NOTE: Previously mutated os.environ['TZ'] globally, which is dangerous.
        # APScheduler CronTrigger supports timezone parameter instead.
        
        # APScheduler uses 0=Monday, 6=Sunday (matches our storage)
        day_name = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][payout_day]
        
        trigger_kwargs = dict(day_of_week=day_name, hour=payout_hour, minute=payout_minute)
        if configured_tz:
            trigger_kwargs["timezone"] = configured_tz
        
        self.scheduler.add_job(
            self.weekly_tally,
            CronTrigger(**trigger_kwargs),
            id="weekly_tally",
            replace_existing=True
        )
        
        tz_display = configured_tz or "system default"
        logger.info(f"Weekly payout scheduled for {day_name.capitalize()} at {payout_hour:02d}:{payout_minute:02d} ({tz_display})")
    
    async def check_missed_payouts(self):
        """On startup, check if any recent weeks are missing payouts and process them"""
        logger.info("Checking for missed weekly payouts...")
        with Session(engine) as session:
            from ..models import WeeklyRollup
            payout_svc = PayoutService(session)
            
            # Check last 4 weeks for missing rollups
            kids = session.exec(select(User).where(User.is_active == True)).all()
            
            for weeks_ago in range(1, 5):  # Check weeks 1-4 weeks back
                target_date = date.today() - timedelta(weeks=weeks_ago)
                week_id = target_date.strftime("%G-W%V")
                
                for kid in kids:
                    # Check if rollup exists for this kid + week
                    stmt = select(WeeklyRollup).where(
                        WeeklyRollup.kid_id == kid.id,
                        WeeklyRollup.week_id == week_id
                    )
                    existing = session.exec(stmt).first()
                    
                    if not existing and weeks_ago <= 2:  # Only auto-process last 2 weeks
                        try:
                            logger.info(f"Processing missed payout: {kid.name} for {week_id}")
                            payout_svc.calculate_and_payout(kid.id, week_id)
                        except Exception as e:
                            logger.error(f"Error processing missed payout for {kid.name} ({week_id}): {e}")
        
        logger.info("Missed payout check complete.")

    async def daily_maintenance(self):
        """Mark yesterday's uncompleted daily chores as INCOMPLETE/MISSED"""
        logger.info("Running Daily Maintenance...")
        with Session(engine) as session:
            yesterday = date.today() - timedelta(days=1)
            week_id = yesterday.strftime("%G-W%V")
            
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
            
            # Mark missed rotation chores for yesterday
            from ..models import RotationGroup, RotationLog
            from .rotation import RotationService
            rotation_svc = RotationService(session)
            
            rot_groups = session.exec(
                select(RotationGroup).where(RotationGroup.archived == False)
            ).all()
            
            for group in rot_groups:
                assigned_kid = rotation_svc.get_assigned_kid(group, yesterday)
                if assigned_kid is None:
                    continue  # Not due yesterday
                
                # Check if log exists
                existing = session.exec(
                    select(RotationLog).where(
                        RotationLog.group_id == group.id,
                        RotationLog.kid_id == assigned_kid,
                        RotationLog.date == yesterday,
                    )
                ).first()
                
                if not existing:
                    missed_log = RotationLog(
                        group_id=group.id,
                        kid_id=assigned_kid,
                        week_id=week_id,
                        date=yesterday,
                        status=ChoreStatus.INCOMPLETE,
                        notes="System: Auto-marked missed rotation",
                    )
                    session.add(missed_log)
            
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
            week_id = yesterday.strftime("%G-W%V")
            
            kids = session.exec(select(User).where(User.is_active == True)).all()
            
            for kid in kids:
                try:
                    logger.info(f"Calculating tally for {kid.name} ({week_id})")
                    payout_svc.calculate_and_payout(kid.id, week_id)
                except Exception as e:
                    logger.error(f"Error tallying for {kid.name}: {e}")
            
        logger.info("Weekly Tally Complete.")
