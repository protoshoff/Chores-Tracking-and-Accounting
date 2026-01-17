from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select, desc
from ..models import LedgerEntry, User, TransactionType

class LedgerService:
    def __init__(self, session: Session):
        self.session = session

    def add_transaction(self, kid_id: int, amount_cents: int, transaction_type: TransactionType, description: str, week_id: Optional[str] = None):
        # 1. Create Entry
        entry = LedgerEntry(
            kid_id=kid_id,
            transaction_type=transaction_type,
            amount_cents=amount_cents,
            description=description,
            timestamp=datetime.utcnow(),
            week_id=week_id
        )
        self.session.add(entry)
        
        # 2. Update Kid Balance
        kid = self.session.get(User, kid_id)
        if kid:
             kid.balance_cents += amount_cents
             self.session.add(kid)
             
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def get_history(self, kid_id: int, limit: int = 20) -> List[LedgerEntry]:
        stmt = select(LedgerEntry).where(LedgerEntry.kid_id == kid_id).order_by(desc(LedgerEntry.timestamp)).limit(limit)
        return self.session.exec(stmt).all()

    def process_payout(self, kid_id: int):
        # 1. Get current balance
        kid = self.session.get(User, kid_id)
        if not kid or kid.balance_cents <= 0:
            return None # Nothing to pay out or invalid
            
        amount_to_pay = kid.balance_cents
        
        # 2. Create PAYOUT transaction
        entry = LedgerEntry(
            kid_id=kid_id,
            transaction_type=TransactionType.PAYOUT,
            amount_cents= -amount_to_pay, # Negative to reduce balance
            description="Allowance Payout",
            timestamp=datetime.utcnow()
        )
        self.session.add(entry)
        
        # 3. Reset Balance
        kid.balance_cents = 0
        self.session.add(kid)
        
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def delete_transaction(self, entry_id: int):
        entry = self.session.get(LedgerEntry, entry_id)
        if not entry:
            return False
            
        # 1. Reverse effect on balance
        kid = self.session.get(User, entry.kid_id)
        if kid:
            # If entry was +100, we subtract 100. If entry was -50, we add 50.
            kid.balance_cents -= entry.amount_cents
            self.session.add(kid)
            
        # 2. Delete entry
        self.session.delete(entry)
        self.session.commit()
        return True
