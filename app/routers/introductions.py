from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_member
from app.db import get_db
from app.models import Member
from app.scoping import get_club_member_or_404, matchable_attributes

router = APIRouter(prefix="/introductions", tags=["introductions"])


@router.get("/{member_a_id}/{member_b_id}")
def generate_reason(
    member_a_id: int,
    member_b_id: int,
    reason: str,
    db: Session = Depends(get_db),
    member: Member = Depends(get_current_member),
):
    # Both members must belong to the caller's club (404 otherwise), and only
    # non-restricted attributes may be used.
    get_club_member_or_404(db, member.club_id, member_a_id)
    get_club_member_or_404(db, member.club_id, member_b_id)

    attrs_a = matchable_attributes(db, member.club_id, member_a_id)
    attrs_b = matchable_attributes(db, member.club_id, member_b_id)

    # Every attribute is stated as fact regardless of its confidence score.
    a_text = "; ".join(a.text for a in attrs_a)
    b_text = "; ".join(b.text for b in attrs_b)
    return {"reason_text": f"Because {a_text} and {b_text} — a good {reason} match."}
