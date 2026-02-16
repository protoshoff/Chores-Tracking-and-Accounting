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

from typing import List
from sqlmodel import select
from ..models import WeeklyRollup, User

class RollupDTO(WeeklyRollup):
    kid_name: str

@router.get("/rollups", response_model=List[RollupDTO])
def get_rollups(session: Session = Depends(get_session)):
    stmt = select(WeeklyRollup, User.name).join(User).order_by(WeeklyRollup.week_id.desc())
    results = session.exec(stmt).all()
    
    dtos = []
    for r, name in results:
        dto = RollupDTO(**r.model_dump())
        dto.kid_name = name
        dtos.append(dto)
    return dtos
