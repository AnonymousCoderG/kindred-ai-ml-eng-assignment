from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import get_db
from app.llm_client import LLMClient
from app.models import Member
from app.services.extraction import run_extraction

router = APIRouter(prefix="/clubs", tags=["extraction"])


class ExtractIn(BaseModel):
    message_ids: list[int] = Field(min_length=1, max_length=100)


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """The real LLM client. Tests replace this with a test double via
    app.dependency_overrides."""
    global _llm_client
    if _llm_client is None:
        from app.llm_real import RealLLMClient  # imported lazily so tests never touch the real client

        try:
            _llm_client = RealLLMClient()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
    return _llm_client


@router.post("/{club_id}/extract-attributes")
def extract_attributes(
    club_id: str,
    payload: ExtractIn,
    admin: Member = Depends(require_admin),  # admin role required (403 otherwise)
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    # The admin must belong to the club in the URL: an admin of another club is refused.
    if club_id != admin.club_id:
        raise HTTPException(status_code=403, detail="admin of a different club")
    return run_extraction(db, club_id, payload.message_ids, llm)
