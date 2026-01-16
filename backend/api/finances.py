from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session
from ..db import get_session
from ..services.payout import PayoutService

router = APIRouter(prefix="/api/finances", tags=["Finances"])

@router.post("/payout/{kid_id}")
def trigger_payout(
    kid_id: int, 
    week_id: str = Body(..., embed=True), # "2023-W43"
    session: Session = Depends(get_session)
):
    service = PayoutService(session)
    try:
        rollup = service.calculate_and_payout(kid_id, week_id)
        return rollup
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
