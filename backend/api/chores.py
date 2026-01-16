from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session
from ..db import get_session
from ..services.chores import ChoreService

router = APIRouter(prefix="/api/chores", tags=["Chores"])

@router.post("/{chore_id}/complete", status_code=201)
def complete_chore(
    chore_id: int, 
    payload: dict = Body(...), # {"kid_id": 1, "date": "2023-10-27"}
    session: Session = Depends(get_session)
):
    kid_id = payload.get("kid_id")
    date_str = payload.get("date")
    
    if not kid_id:
        raise HTTPException(status_code=400, detail="kid_id required")
        
    target_date = date.today()
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid date format YYYY-MM-DD")

    service = ChoreService(session)
    log = service.mark_complete(chore_id, kid_id, target_date)
    return {"status": log.status, "message": "Marked complete", "log_id": log.id}
