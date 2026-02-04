#!/usr/bin/env python3
"""
Balance Reconciliation Script
Verifies and fixes balance inconsistencies between users.balance and SUM(ledger_entries.amount)

Usage:
    python3 scripts/reconcile_balances.py [--fix] [--db-path /path/to/chores.db]
"""

import sys
import argparse
from sqlalchemy import create_engine, text

def reconcile_balances(db_path, fix=False):
    """Check and optionally fix balance discrepancies"""
    engine = create_engine(f"sqlite:///{db_path}")
    
    query = """
    SELECT 
        u.id, 
        u.name,
        u.balance AS stored_balance,
        COALESCE(SUM(l.amount), 0) AS calculated_balance,
        u.balance - COALESCE(SUM(l.amount), 0) AS discrepancy
    FROM users u
    LEFT JOIN ledger_entries l ON u.id = l.kid_id
    GROUP BY u.id, u.name, u.balance
    """
    
    print("=" * 70)
    print("BALANCE RECONCILIATION REPORT")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        
        discrepancies = []
        
        print(f"{'ID':<5} {'Name':<15} {'Stored':<12} {'Calculated':<12} {'Discrepancy':<12}")
        print("-" * 70)
        
        for row in rows:
            kid_id, name, stored, calculated, discrepancy = row
            status = "✓ OK" if abs(discrepancy) < 0.01 else "✗ ERROR"
            
            print(f"{kid_id:<5} {name:<15} ${stored:<11.2f} ${calculated:<11.2f} ${discrepancy:<11.2f} {status}")
            
            if abs(discrepancy) >= 0.01:
                discrepancies.append((kid_id, name, stored, calculated, discrepancy))
        
        print("=" * 70)
        
        if discrepancies:
            print(f"\n⚠️  Found {len(discrepancies)} discrepancy(ies)")
            
            if fix:
                print("\n🔧 FIX MODE ENABLED - Correcting balances...")
                for kid_id, name, stored, calculated, discrepancy in discrepancies:
                    print(f"\n  Updating {name} (ID: {kid_id})")
                    print(f"    Old balance: ${stored:.2f}")
                    print(f"    New balance: ${calculated:.2f}")
                    
                    update_query = text("UPDATE users SET balance = :new_balance WHERE id = :kid_id")
                    conn.execute(update_query, {"new_balance": round(calculated, 2), "kid_id": kid_id})
                
                conn.commit()
                print("\n✅ All balances corrected!")
            else:
                print("\n💡 Run with --fix flag to automatically correct balances")
        else:
            print("\n✅ All balances are correct!")
    
    return len(discrepancies)

def main():
    parser = argparse.ArgumentParser(description="Reconcile user balances with ledger entries")
    parser.add_argument("--fix", action="store_true", help="Automatically fix discrepancies")
    parser.add_argument("--db-path", default="./chores.db", help="Path to SQLite database")
    
    args = parser.parse_args()
    
    try:
        discrepancy_count = reconcile_balances(args.db_path, args.fix)
        sys.exit(discrepancy_count)  # Exit code = number of discrepancies
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
