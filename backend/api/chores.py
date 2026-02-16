from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from ..db import get_session
from ..services.chores import ChoreService

router = APIRouter(prefix="/api/chores", tags=["Chores"])


class CompleteChoreRequest(BaseModel):
    kid_id: int
    date: Optional[str] = None  # "YYYY-MM-DD", defaults to today


@router.post("/{chore_id}/complete", status_code=201)
def complete_chore(
    chore_id: int,
    payload: CompleteChoreRequest,
    session: Session = Depends(get_session)
):
    target_date = date.today()
    if payload.date:
        try:
            target_date = date.fromisoformat(payload.date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format YYYY-MM-DD")

    service = ChoreService(session)
    log = service.mark_complete(chore_id, payload.kid_id, target_date)
    return {"status": log.status, "message": "Marked complete", "log_id": log.id}
