"""Rotation chore service — determines who does what and when."""
from datetime import date, timedelta
from typing import List, Optional, Tuple
from sqlmodel import Session, select
from ..models import (
    RotationGroup, RotationMember, RotationLog, RotationFrequency,
    ChoreStatus, User
)


class RotationService:
    def __init__(self, session: Session):
        self.session = session

    def _get_active_members(self, group: RotationGroup) -> List[RotationMember]:
        """Get active (non-deactivated) members in position order."""
        stmt = (
            select(RotationMember)
            .join(User, RotationMember.kid_id == User.id)
            .where(
                RotationMember.group_id == group.id,
                User.is_active == True,
            )
            .order_by(RotationMember.position)
        )
        return list(self.session.exec(stmt).all())

    def get_assigned_kid(self, group: RotationGroup, target_date: date) -> Optional[int]:
        """Determine which kid is assigned to a rotation group on a given date.
        
        Returns kid_id or None if the chore is not due on this date.
        """
        members = self._get_active_members(group)
        if not members:
            return None

        days_since_start = (target_date - group.start_date).days
        if days_since_start < 0:
            return None  # Before rotation started

        if group.frequency == RotationFrequency.ALTERNATING_DAILY:
            # Due every day, rotating through members
            position = days_since_start % len(members)
            return members[position].kid_id

        elif group.frequency == RotationFrequency.EVERY_OTHER_DAY:
            # Due every 2nd day from start_date
            if days_since_start % 2 != 0:
                return None  # Not due today
            rotation_index = (days_since_start // 2) % len(members)
            return members[rotation_index].kid_id

        elif group.frequency == RotationFrequency.BIWEEKLY:
            # Due every 2 weeks on the same weekday as start_date
            if target_date.weekday() != group.start_date.weekday():
                return None  # Not the right day of week
            weeks_since_start = days_since_start // 7
            if weeks_since_start % 2 != 0:
                return None  # Off-week
            rotation_index = (weeks_since_start // 2) % len(members)
            return members[rotation_index].kid_id

        return None

    def is_due_today(self, group: RotationGroup, target_date: date) -> bool:
        """Check if a rotation chore is due on a given date (for any kid)."""
        return self.get_assigned_kid(group, target_date) is not None

    def get_todays_rotation_chores(self, kid_id: int, target_date: Optional[date] = None) -> List[dict]:
        """Get all rotation chores assigned to a kid for a given date."""
        if target_date is None:
            target_date = date.today()

        # Get all active rotation groups
        stmt = select(RotationGroup).where(RotationGroup.archived == False)
        groups = self.session.exec(stmt).all()

        result = []
        for group in groups:
            assigned_kid = self.get_assigned_kid(group, target_date)
            if assigned_kid == kid_id:
                # Check if there's already a log for today
                log = self._get_log(group.id, kid_id, target_date)
                status = log.status if log else ChoreStatus.INCOMPLETE

                # Get all member names for display
                members = self._get_active_members(group)
                other_names = [
                    m.kid.name for m in members 
                    if m.kid_id != kid_id and m.kid
                ]

                result.append({
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "frequency": group.frequency,
                    "status": status,
                    "is_rotation": True,
                    "shared_with": other_names,
                    "log_id": log.id if log else None,
                })

        return result

    def mark_complete(self, group_id: int, kid_id: int, target_date: Optional[date] = None) -> RotationLog:
        """Mark a rotation chore as complete (PENDING approval)."""
        from datetime import datetime, timezone
        
        if target_date is None:
            target_date = date.today()
        
        week_id = target_date.strftime("%G-W%V")

        # Check for existing log
        existing = self._get_log(group_id, kid_id, target_date)
        if existing:
            existing.status = ChoreStatus.PENDING
            existing.completed_at = datetime.now(timezone.utc)
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        log = RotationLog(
            group_id=group_id,
            kid_id=kid_id,
            week_id=week_id,
            date=target_date,
            status=ChoreStatus.PENDING,
            completed_at=datetime.now(timezone.utc),
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def _get_log(self, group_id: int, kid_id: int, target_date: date) -> Optional[RotationLog]:
        stmt = select(RotationLog).where(
            RotationLog.group_id == group_id,
            RotationLog.kid_id == kid_id,
            RotationLog.date == target_date,
        )
        return self.session.exec(stmt).first()

    def calculate_expected_instances(self, kid_id: int, week_id: str, reference_date: Optional[date] = None) -> int:
        """Calculate how many rotation instances a kid is expected to complete in a given week."""
        # Parse week_id to get the Monday of that week
        if reference_date is None:
            import re
            match = re.match(r"(\d{4})-W(\d{2})", week_id)
            if not match:
                return 0
            year, week_num = int(match.group(1)), int(match.group(2))
            # ISO week: Monday of week 1 is the Monday of the week containing Jan 4
            from datetime import date as dt_date
            jan4 = dt_date(year, 1, 4)
            monday_w1 = jan4 - timedelta(days=jan4.weekday())
            reference_date = monday_w1 + timedelta(weeks=week_num - 1)

        # reference_date should be the Monday of the week
        monday = reference_date - timedelta(days=reference_date.weekday())
        
        stmt = select(RotationGroup).where(RotationGroup.archived == False)
        groups = self.session.exec(stmt).all()
        
        expected = 0
        for group in groups:
            # Check if this kid is a member
            members = self._get_active_members(group)
            if not any(m.kid_id == kid_id for m in members):
                continue
            
            # Count how many days this week the kid is assigned
            for day_offset in range(7):
                day = monday + timedelta(days=day_offset)
                if self.get_assigned_kid(group, day) == kid_id:
                    expected += 1

        return expected

    def count_completed_instances(self, kid_id: int, week_id: str) -> int:
        """Count approved rotation logs for a kid in a given week."""
        stmt = select(RotationLog).where(
            RotationLog.kid_id == kid_id,
            RotationLog.week_id == week_id,
            RotationLog.status == ChoreStatus.APPROVED,
        )
        return len(self.session.exec(stmt).all())

    def get_schedule(self, group_id: int, weeks: int = 2) -> List[dict]:
        """Get a schedule preview for a rotation group."""
        group = self.session.get(RotationGroup, group_id)
        if not group:
            return []

        today = date.today()
        monday = today - timedelta(days=today.weekday())
        
        schedule = []
        for day_offset in range(weeks * 7):
            day = monday + timedelta(days=day_offset)
            assigned = self.get_assigned_kid(group, day)
            if assigned is not None:
                kid = self.session.get(User, assigned)
                schedule.append({
                    "date": day.isoformat(),
                    "kid_id": assigned,
                    "kid_name": kid.name if kid else "Unknown",
                    "is_today": day == today,
                })

        return schedule

    def get_pending_approvals(self) -> List[dict]:
        """Get all pending rotation logs for approval."""
        stmt = (
            select(RotationLog, User, RotationGroup)
            .join(User, RotationLog.kid_id == User.id)
            .join(RotationGroup, RotationLog.group_id == RotationGroup.id)
            .where(RotationLog.status == ChoreStatus.PENDING)
            .order_by(RotationLog.completed_at)
        )
        results = self.session.exec(stmt).all()

        return [
            {
                "id": log.id,
                "kid_id": log.kid_id,
                "kid_name": kid.name,
                "group_id": log.group_id,
                "chore_name": f"🔄 {group.name}",
                "date": log.date.isoformat(),
                "status": log.status,
                "completed_at": log.completed_at,
                "reward": 0.0,  # Rotation chores don't have individual rewards
                "is_rotation": True,
            }
            for log, kid, group in results
        ]
