import pytest
from fastapi.testclient import TestClient

from app.embeddings import embedding_client
from app.main import app
from app.models import Club, KnowledgeChunk, Member, MemberAttribute

client = TestClient(app)


def _add_chunk(db, club_id, title, body):
    db.add(
        KnowledgeChunk(
            club_id=club_id,
            title=title,
            body=body,
            embedding=embedding_client.embed(body),
        )
    )


def _two_clubs(db):
    db.add(Club(id="riverside", name="Riverside"))
    db.add(Club(id="oakhurst", name="Oakhurst"))
    db.commit()


# ---------- Issue 1: knowledge query must only return the caller's club ----------


@pytest.mark.parametrize("club_id", ["riverside", "oakhurst"])
def test_knowledge_query_only_returns_own_club_chunks(db, club_id):
    _two_clubs(db)
    db.add(Member(club_id="riverside", name="R", email="r@example.com", token="tok-r", role="member"))
    db.add(Member(club_id="oakhurst", name="O", email="o@example.com", token="tok-o", role="member"))
    # 3 chunks per club = 6 total, more than the endpoint's limit of 5,
    # so an unscoped search is guaranteed to mix clubs.
    for i in range(3):
        _add_chunk(db, "riverside", f"R{i}", f"Riverside guest fees rule {i}")
        _add_chunk(db, "oakhurst", f"O{i}", f"Oakhurst guest fees rule {i}")
    db.commit()

    token = "tok-r" if club_id == "riverside" else "tok-o"
    resp = client.get(
        f"/clubs/{club_id}/knowledge/query",
        params={"q": "guest fees"},
        headers={"X-Member-Token": token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3  # all of this club's chunks, none of the other club's
    assert {r["club_id"] for r in body} == {club_id}


# ---------- Issue 2: introductions must be scoped to the caller's club ----------


def _intro_setup(db):
    _two_clubs(db)
    r1 = Member(club_id="riverside", name="R1", email="r1@example.com", token="tok-r1", role="member")
    r2 = Member(club_id="riverside", name="R2", email="r2@example.com", token="tok-r2", role="member")
    o1 = Member(club_id="oakhurst", name="O1", email="o1@example.com", token="tok-o1", role="member")
    o2 = Member(club_id="oakhurst", name="O2", email="o2@example.com", token="tok-o2", role="member")
    db.add_all([r1, r2, o1, o2])
    db.commit()
    return r1, r2, o1, o2


def test_introduction_rejects_two_members_of_another_club(db):
    r1, r2, o1, o2 = _intro_setup(db)
    db.add(MemberAttribute(member_id=o1.id, club_id="oakhurst", kind="offer", text="secret offer", confidence=0.9))
    db.commit()

    resp = client.get(
        f"/introductions/{o1.id}/{o2.id}",
        params={"reason": "business"},
        headers={"X-Member-Token": "tok-r1"},
    )
    assert resp.status_code == 404
    assert "secret offer" not in resp.text


def test_introduction_rejects_when_only_one_member_is_foreign(db):
    r1, r2, o1, o2 = _intro_setup(db)

    resp = client.get(
        f"/introductions/{r1.id}/{o1.id}",
        params={"reason": "business"},
        headers={"X-Member-Token": "tok-r1"},
    )
    assert resp.status_code == 404


def test_introduction_unknown_member_is_404(db):
    r1, r2, o1, o2 = _intro_setup(db)

    resp = client.get(
        f"/introductions/{r1.id}/999999",
        params={"reason": "business"},
        headers={"X-Member-Token": "tok-r1"},
    )
    assert resp.status_code == 404


def test_introduction_never_includes_restricted_attributes(db):
    r1, r2, o1, o2 = _intro_setup(db)
    db.add(MemberAttribute(member_id=r1.id, club_id="riverside", kind="need", text="needs a CFO", confidence=0.9))
    db.add(
        MemberAttribute(
            member_id=r2.id, club_id="riverside", kind="context", text="has a chronic condition", confidence=0.9, restricted=True
        )
    )
    db.add(MemberAttribute(member_id=r2.id, club_id="riverside", kind="offer", text="offers CFO services", confidence=0.9))
    db.commit()

    resp = client.get(
        f"/introductions/{r1.id}/{r2.id}",
        params={"reason": "business"},
        headers={"X-Member-Token": "tok-r1"},
    )
    assert resp.status_code == 200
    text = resp.json()["reason_text"]
    assert "CFO" in text  # same-club introductions still work
    assert "chronic condition" not in text  # restricted data never leaks
