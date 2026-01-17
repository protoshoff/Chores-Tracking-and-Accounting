from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session
from ..db import get_session
from ..models import LedgerEntry, TransactionType
from ..services.ledger import LedgerService

router = APIRouter(prefix="/api/ledger", tags=["Ledger"])

@router.post("/transaction", status_code=201)
def add_transaction(
    payload: dict = Body(...), # {kid_id: 1, amount_cents: 100, type: "BONUS", description: "Good job"}
    session: Session = Depends(get_session)
):
    kid_id = payload.get("kid_id")
    amount = payload.get("amount_cents")
    
    if kid_id is None or amount is None:
        raise HTTPException(status_code=400, detail="Missing kid_id or amount_cents")
        
    t_type = payload.get("type", "ADJUSTMENT")
    try:
        t_enum = TransactionType(t_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid TransactionType")
        
    service = LedgerService(session)
    entry = service.add_transaction(
        kid_id=kid_id,
        amount_cents=amount,
        transaction_type=t_enum,
        description=payload.get("description", "Manual Entry")
    )
    return entry

@router.get("/{kid_id}/history", response_model=List[LedgerEntry])
def get_history(kid_id: int, session: Session = Depends(get_session)):
    service = LedgerService(session)
    return service.get_history(kid_id)

@router.post("/{kid_id}/payout", status_code=201)
def payout_kid(kid_id: int, session: Session = Depends(get_session)):
    service = LedgerService(session)
    entry = service.process_payout(kid_id)
    if not entry:
         raise HTTPException(status_code=400, detail="Nothing to pay out or kid not found")
    return entry

@router.delete("/transaction/{entry_id}")
def delete_transaction(entry_id: int, session: Session = Depends(get_session)):
    service = LedgerService(session)
    success = service.delete_transaction(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "deleted", "id": entry_id}
