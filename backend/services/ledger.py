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
