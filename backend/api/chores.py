from datetime import date
from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from ..db import get_session
from ..services.chores import ChoreService

router = APIRouter(prefix="/api/chores", tags=["Chores"])

# Completion audit log — writes to /var/lib/chores_app/completion.log
_completion_logger = logging.getLogger("chores.completion")
if not _completion_logger.handlers:
    import os
    _log_dir = os.getenv("CHORES_DATA_DIR", "/var/lib/chores_app")
    try:
        _fh = logging.FileHandler(os.path.join(_log_dir, "completion.log"))
        _fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        _completion_logger.addHandler(_fh)
        _completion_logger.setLevel(logging.INFO)
    except Exception:
        pass  # Dev machine without /var/lib — skip file logging


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
    _completion_logger.info(
        f"CHORE kid={payload.kid_id} chore={chore_id} date={target_date} "
        f"log_id={log.id} status={log.status}"
    )
    return {"status": log.status, "message": "Marked complete", "log_id": log.id}
