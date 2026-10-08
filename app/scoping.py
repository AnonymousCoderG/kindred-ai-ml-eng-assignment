"""Club-scoped data access.

Every read of member or attribute data on behalf of a caller should go through
these helpers, so the caller's club and the `restricted` flag are applied in one
place instead of being repeated (and forgotten) in each router or service.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session

from app.models import Member, MemberAttribute


def get_club_member_or_404(db: Session, club_id: str, member_id: int) -> Member:
    """Return the member only if they belong to `club_id`.

    A member of another club and a member that does not exist both give 404, so
    the response never confirms that a member exists in a different club.
    """
    member = db.query(Member).filter(Member.id == member_id, Member.club_id == club_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="member not found")
    return member


def _matchable(query: Query, club_id: str) -> Query:
    """THE restricted-attribute check. Restricted attributes (health, clinical,
    psychometric) are excluded here, in the data-access layer, for everything that
    feeds matching, ranking or introductions. Nothing else defines "matchable"."""
    return query.filter(
        MemberAttribute.club_id == club_id,
        MemberAttribute.restricted.is_(False),
    )


def matchable_attributes(
    db: Session, club_id: str, member_id: int, min_confidence: float = 0.0
) -> list[MemberAttribute]:
    """Attributes that are allowed to feed matching and introductions."""
    return (
        _matchable(db.query(MemberAttribute), club_id)
        .filter(
            MemberAttribute.member_id == member_id,
            MemberAttribute.confidence >= min_confidence,
        )
        .order_by(MemberAttribute.id)
        .all()
    )


def matchable_profile_texts(db: Session, club_id: str) -> dict[int, str]:
    """member_id -> profile text for every member of the club, built only from
    matchable attributes, with a single query (no per-member queries)."""
    rows = (
        _matchable(db.query(MemberAttribute.member_id, MemberAttribute.text), club_id)
        .order_by(MemberAttribute.id)
        .all()
    )
    parts: dict[int, list[str]] = {}
    for member_id, text in rows:
        parts.setdefault(member_id, []).append(text)
    return {member_id: " | ".join(texts) for member_id, texts in parts.items()}
