from app.embeddings import embedding_client
from app.models import Club, Member, MemberAttribute
from app.services.matching_service import build_member_profile_text, cosine_similarity, rank_candidates

RESTRICTED_TEXT = "has a chronic condition"


def _setup(db):
    db.add(Club(id="riverside", name="Riverside"))
    db.commit()
    r1 = Member(club_id="riverside", name="R1", email="r1@example.com", token="tok-r1", role="member")
    r2 = Member(club_id="riverside", name="R2", email="r2@example.com", token="tok-r2", role="member")
    r3 = Member(club_id="riverside", name="R3", email="r3@example.com", token="tok-r3", role="member")
    db.add_all([r1, r2, r3])
    db.commit()
    db.add_all(
        [
            MemberAttribute(member_id=r1.id, club_id="riverside", kind="need", text="needs a CFO", confidence=0.9),
            MemberAttribute(member_id=r2.id, club_id="riverside", kind="offer", text="angel investor", confidence=0.9),
            MemberAttribute(
                member_id=r2.id, club_id="riverside", kind="context", text=RESTRICTED_TEXT, confidence=0.9, restricted=True
            ),
            # r3 has ONLY a restricted attribute
            MemberAttribute(
                member_id=r3.id, club_id="riverside", kind="context", text=RESTRICTED_TEXT, confidence=0.9, restricted=True
            ),
        ]
    )
    db.commit()
    # Simulates data built before the fix: a stored embedding made from restricted text.
    r2.profile_embedding = embedding_client.embed(f"angel investor | {RESTRICTED_TEXT}")
    r3.profile_embedding = embedding_client.embed(RESTRICTED_TEXT)
    db.commit()
    return r1, r2, r3


def test_profile_text_excludes_restricted_attributes(db):
    r1, r2, r3 = _setup(db)

    assert build_member_profile_text(r2, db) == "angel investor"
    assert build_member_profile_text(r3, db) == ""


def test_ranking_never_embeds_or_uses_restricted_text(db, monkeypatch):
    r1, r2, r3 = _setup(db)
    seen = []
    original = embedding_client.embed

    def spy(text):
        seen.append(text)
        return original(text)

    monkeypatch.setattr(embedding_client, "embed", spy)

    results = rank_candidates(r1, "business", db)

    assert seen, "ranking should have embedded something"
    assert all(RESTRICTED_TEXT not in text for text in seen)  # restricted text never reaches the embedder
    assert [r["member_id"] for r in results] == [r2.id]  # r3 has nothing matchable, so is not ranked
    expected = cosine_similarity(original("needs a CFO"), original("angel investor"))
    assert results[0]["score"] == round(float(expected), 4)  # stored (restricted-tainted) embedding ignored
