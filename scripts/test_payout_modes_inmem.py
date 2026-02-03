#!/usr/bin/env python3
"""
Test script for payout calculation modes (using in-memory database)
Tests both All-or-Nothing and Proportional payout modes with instance-based counting

Run from project root:
    cd /Users/charlesshoffner/Documents/CodingProjects/Chores-Tracking-and-Accounting
    source venv/bin/activate
    python3 scripts/test_payout_modes_inmem.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlmodel import SQLModel, create_engine, Session, select, delete
from backend.models import User, Chore, ChoreLog, ChoreStatus, Settings, WeeklyRollup, Frequency
from backend.services.payout import PayoutService
from datetime import date, timedelta

# Create in-memory database
engine = create_engine("sqlite:///:memory:", echo=False)

def setup_database():
    """Create all tables in the in-memory database"""
    SQLModel.metadata.create_all(engine)

def cleanup_test_data(session: Session):
    """Remove any existing test data"""
    session.exec(delete(ChoreLog).where(ChoreLog.kid_id == 999))
    session.exec(delete(Chore).where(Chore.kid_id == 999))
    session.exec(delete(WeeklyRollup).where(WeeklyRollup.kid_id == 999))
    session.exec(delete(User).where(User.id == 999))
    session.commit()

def create_test_kid(session: Session) -> User:
    """Create a test kid with $20 allowance"""
    kid = User(
        id=999,
        name="Test Kid",
        allowance=20.0,
        balance=0.0
    )
    session.add(kid)
    session.commit()
    session.refresh(kid)
    return kid

def create_test_chores(session: Session, kid_id: int) -> list:
    """Create 3 daily chores and 2 weekly chores (23 total instances)"""
    chores = []
    
    # 3 Daily chores (21 instances per week)
    for i in range(3):
        chore = Chore(
            kid_id=kid_id,
            name=f"Daily Chore {i+1}",
            reward=1.0,
            frequency=Frequency.DAILY,
            archived=False
        )
        chores.append(chore)
        session.add(chore)
    
    # 2 Weekly chores (2 instances per week)
    for i in range(2):
        chore = Chore(
            kid_id=kid_id,
            name=f"Weekly Chore {i+1}",
            reward=1.0,
            frequency=Frequency.WEEKLY,
            archived=False
        )
        chores.append(chore)
        session.add(chore)
    
    session.commit()
    for chore in chores:
        session.refresh(chore)
    return chores

def create_chore_logs(session: Session, chores: list, kid_id: int, week_id: str, completion_pct: float):
    """Create approved chore logs for specified completion percentage
    
    Args:
        chores: List of chores to log (first 3 are daily, last 2 are weekly)
        completion_pct: 0.0 to 1.0 representing percentage of chores to approve
    """
    total_instances = 23  # 3*7 + 2*1
    instances_to_approve = int(total_instances * completion_pct)
    
    week_start = date.today() - timedelta(days=date.today().weekday())  # Monday
    approved_count = 0
    
    # Approve daily chore instances
    for day_offset in range(7):
        log_date = week_start + timedelta(days=day_offset)
        for chore in chores[:3]:  # First 3 are daily
            if approved_count < instances_to_approve:
                log = ChoreLog(
                    chore_id=chore.id,
                    kid_id=kid_id,
                    week_id=week_id,
                    date=log_date,
                    status=ChoreStatus.APPROVED
                )
                session.add(log)
                approved_count += 1
    
    # Approve weekly chore instances
    for chore in chores[3:]:  # Last 2 are weekly
        if approved_count < instances_to_approve:
            log = ChoreLog(
                chore_id=chore.id,
                kid_id=kid_id,
                week_id=week_id,
                date=week_start,
                status=ChoreStatus.APPROVED
            )
            session.add(log)
            approved_count += 1
    
    session.commit()
    print(f"  → Created {approved_count} approved chore logs ({completion_pct*100:.0f}% completion)")

def set_payout_config(session: Session, mode: str, threshold: int = 80):
    """Set payout mode and threshold in settings"""
    # Set payout mode
    mode_setting = session.get(Settings, "payout_mode")
    if mode_setting:
        mode_setting.value = mode
    else:
        mode_setting = Settings(key="payout_mode", value=mode)
    session.add(mode_setting)
    
    # Set threshold
    threshold_setting = session.get(Settings, "payout_threshold")
    if threshold_setting:
        threshold_setting.value = str(threshold)
    else:
        threshold_setting = Settings(key="payout_threshold", value=str(threshold))
    session.add(threshold_setting)
    
    session.commit()

def run_test(session: Session, test_name: str, mode: str, threshold: int, completion_pct: float, expected_payout: float):
    """Run a single payout test"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    print(f"  Mode: {mode}")
    print(f"  Threshold: {threshold}%")
    print(f"  Completion: {completion_pct*100:.0f}% ({int(23*completion_pct)}/23 instances)")
    print(f"  Expected Payout: ${expected_payout:.2f}")
    
    # Setup
    cleanup_test_data(session)
    kid = create_test_kid(session)
    chores = create_test_chores(session, kid.id)
    week_id = "2024-W05"
    
    set_payout_config(session, mode, threshold)
    create_chore_logs(session, chores, kid.id, week_id, completion_pct)
    
    # Execute payout
    payout_service = PayoutService(session)
    rollup = payout_service.calculate_and_payout(kid.id, week_id)
    
    # Verify
    actual_payout = rollup.payout
    print(f"  → Actual Payout: ${actual_payout:.2f}")
    
    # Check if test passed
    if abs(actual_payout - expected_payout) < 0.01:
        print("  ✅ TEST PASSED")
        return True
    else:
        print(f"  ❌ TEST FAILED - Expected ${expected_payout:.2f}, got ${actual_payout:.2f}")
        return False

def main():
    print("=" * 70)
    print("PAYOUT MODES TEST SUITE")
    print("=" * 70)
    print("Testing instance-based calculation:")
    print("  - 3 daily chores × 7 days = 21 instances")
    print("  - 2 weekly chores × 1 week = 2 instances")
    print("  - Total: 23 expected instances per week")
    print("  - Test Kid Allowance: $20.00")
    print("=" * 70)
    
    # Setup database
    setup_database()
    
    results = []
    
    with Session(engine) as session:
        # Test 1: All-or-Nothing @ 80% threshold with 50% completion
        # Expected: $0 (50% < 80%)
        results.append(run_test(
            session, 
            "All-or-Nothing (80% threshold) - 50% completion",
            "ALL_OR_NOTHING", 
            80, 
            0.50, 
            0.0
        ))
        
        # Test 2: All-or-Nothing @ 40% threshold with 50% completion
        # Expected: $20 (50% >= 40%)
        results.append(run_test(
            session, 
            "All-or-Nothing (40% threshold) - 50% completion",
            "ALL_OR_NOTHING", 
            40, 
            0.50, 
            20.0
        ))
        
        # Test 3: Proportional with ~48% completion (11/23 instances)
        # Expected: $9.57 ((11/23) * $20)
        results.append(run_test(
            session, 
            "Proportional - ~48% completion (11/23 instances)",
            "PRORATED", 
            80,  # Threshold ignored in proportional mode
            0.50,  # Will create 11 instances (int(23*0.5) = 11)  
            9.57  # (11/23) * 20 = 9.57
        ))
        
        # Test 4: Proportional with 100% completion
        # Expected: $20 (100% of $20)
        results.append(run_test(
            session, 
            "Proportional - 100% completion",
            "PRORATED", 
            80, 
            1.0, 
            20.0
        ))
        
        # Test 5: Proportional with 25% completion (6/23 instances ≈ 26.09%)
        # Expected: $5.22 (26.09% of $20)
        results.append(run_test(
            session, 
            "Proportional - ~26% completion",
            "PRORATED", 
            80, 
            6/23,  # 6 out of 23 instances
            5.22  # (6/23) * 20 ≈ 5.22
        ))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
