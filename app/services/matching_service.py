import math

from sqlalchemy.orm import Session

from app.embeddings import embedding_client
from app.models import Member
from app.scoping import matchable_attributes, matchable_profile_texts


def build_member_profile_text(member: Member, db: Session) -> str:
    # Only matchable (non-restricted) attributes. The restricted check lives in
    # app/scoping.py, so this function cannot forget it.
    return " | ".join(a.text for a in matchable_attributes(db, member.club_id, member.id))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rank_candidates(member: Member, reason: str, db: Session) -> list[dict]:
    candidates = (
        db.query(Member)
        .filter(Member.club_id == member.club_id, Member.id != member.id)
        .all()
    )

    # One query for every member's profile text, restricted attributes excluded.
    texts = matchable_profile_texts(db, member.club_id)
    # Computed once, outside the loop.
    query_vec = embedding_client.embed(texts.get(member.id, ""))

    results = []
    for candidate in candidates:
        candidate_text = texts.get(candidate.id)
        if not candidate_text:
            continue  # nothing matchable about this member
        # The stored profile_embedding is deliberately NOT used: rows seeded or
        # written earlier were built from every attribute, restricted ones included.
        candidate_vec = embedding_client.embed(candidate_text)
        score = cosine_similarity(query_vec, [float(v) for v in candidate_vec])
        results.append({"member_id": candidate.id, "name": candidate.name, "score": round(float(score), 4)})

    results.sort(key=lambda r: -r["score"])
    return results
