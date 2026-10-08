from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.llm_client import FakeLLMClient
from app.llm_errors import PermanentLLMError, TransientLLMError
from app.main import app
from app.models import Club, ConversationMessage, Member, MemberAttribute
from app.routers.extraction import get_llm_client
from app.scoping import matchable_attributes
from app.services.extraction import run_extraction

client = TestClient(app)

NEED = {"kind": "need", "text": "raising a seed round", "confidence": 0.9, "restricted": False}
HEALTH = {"kind": "context", "text": "in therapy", "confidence": 0.9, "restricted": True}


class ScriptedLLM:
    """Test double: behaviour chosen by message text. A behaviour is either a list
    (returned) or an exception (raised)."""

    def __init__(self, default, behaviours=None):
        self.default = default
        self.behaviours = behaviours or {}
        self.calls = []

    def extract_attributes(self, message_text):
        self.calls.append(message_text)
        behaviour = self.behaviours.get(message_text, self.default)
        if isinstance(behaviour, Exception):
            raise behaviour
        return behaviour


class FlakyLLM:
    """Fails with a transient error `failures` times, then succeeds."""

    def __init__(self, failures, result, error=None):
        self.failures = failures
        self.result = result
        self.error = error or TransientLLMError("503 service unavailable")
        self.calls = []

    def extract_attributes(self, message_text):
        self.calls.append(message_text)
        if len(self.calls) <= self.failures:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def _use(llm):
    app.dependency_overrides[get_llm_client] = lambda: llm


def _setup(db, n_messages=1):
    db.add_all([Club(id="riverside", name="Riverside"), Club(id="oakhurst", name="Oakhurst")])
    db.commit()
    admin = Member(club_id="riverside", name="Admin", email="admin@example.com", token="tok-admin", role="admin")
    member = Member(club_id="riverside", name="M", email="m@example.com", token="tok-member", role="member")
    other_admin = Member(club_id="oakhurst", name="OA", email="oa@example.com", token="tok-other-admin", role="admin")
    other_member = Member(club_id="oakhurst", name="OM", email="om@example.com", token="tok-om", role="member")
    db.add_all([admin, member, other_admin, other_member])
    db.commit()
    messages = [
        ConversationMessage(member_id=member.id, club_id="riverside", body=f"message {i + 1}") for i in range(n_messages)
    ]
    foreign = ConversationMessage(member_id=other_member.id, club_id="oakhurst", body="foreign message")
    db.add_all(messages + [foreign])
    db.commit()
    return SimpleNamespace(member=member, messages=messages, foreign=foreign)


def _post(ids, token="tok-admin", club="riverside"):
    return client.post(
        f"/clubs/{club}/extract-attributes", json={"message_ids": ids}, headers={"X-Member-Token": token}
    )


def _rows(db, message_id=None):
    db.expire_all()
    q = db.query(MemberAttribute)
    if message_id is not None:
        q = q.filter(MemberAttribute.source_message_id == message_id)
    return q.all()


# ---------- happy path ----------


def test_happy_path_writes_attributes_with_restricted_flag(db):
    s = _setup(db)
    llm = FakeLLMClient(canned_response=[NEED, HEALTH])
    _use(llm)

    resp = _post([s.messages[0].id])

    assert resp.status_code == 200
    body = resp.json()
    assert body["results"][0]["status"] == "processed"
    assert body["summary"]["attributes_created"] == 2
    rows = _rows(db, s.messages[0].id)
    assert {(r.kind, r.restricted) for r in rows} == {("need", False), ("context", True)}
    assert all(r.club_id == "riverside" and r.member_id == s.member.id for r in rows)


def test_invalid_llm_items_are_dropped_not_written(db):
    s = _setup(db)
    bad_kind = {"kind": "hobby", "text": "x", "confidence": 0.5, "restricted": False}
    bad_confidence = {"kind": "offer", "text": "y", "confidence": 1.5, "restricted": False}
    _use(FakeLLMClient(canned_response=[NEED, bad_kind, bad_confidence]))

    resp = _post([s.messages[0].id])

    result = resp.json()["results"][0]
    assert result["attributes_created"] == 1
    assert result["attributes_dropped"] == 2
    assert len(_rows(db)) == 1


# ---------- idempotency ----------


def test_rerunning_a_batch_creates_no_duplicates(db):
    s = _setup(db, n_messages=2)
    llm = FakeLLMClient(canned_response=[NEED])
    _use(llm)
    ids = [m.id for m in s.messages]

    first = _post(ids).json()
    second = _post(ids).json()

    assert first["summary"]["processed"] == 2
    assert second["summary"]["skipped_already_processed"] == 2
    assert second["summary"]["processed"] == 0
    assert len(_rows(db)) == 2
    assert len(llm.calls) == 2  # the second run made no LLM calls


# ---------- partial failure ----------


def test_one_permanent_failure_does_not_fail_the_batch(db):
    s = _setup(db, n_messages=5)
    llm = ScriptedLLM(default=[NEED], behaviours={"message 3": PermanentLLMError("400 bad request")})
    _use(llm)
    ids = [m.id for m in s.messages]

    resp = _post(ids)

    assert resp.status_code == 200
    statuses = [r["status"] for r in resp.json()["results"]]
    assert statuses == ["processed", "processed", "failed", "processed", "processed"]
    assert len(_rows(db)) == 4
    assert _rows(db, s.messages[2].id) == []  # nothing written for the failed message
    assert len(llm.calls) == 5  # a permanent error is not retried

    # Re-running only retries the failed message; the other four are skipped.
    again = _post(ids).json()
    assert again["summary"]["skipped_already_processed"] == 4
    assert again["summary"]["failed"] == 1
    assert llm.calls[-1] == "message 3" and len(llm.calls) == 6


# ---------- retry strategy ----------


def test_transient_errors_are_retried_with_exponential_backoff(db):
    s = _setup(db)
    llm = FlakyLLM(failures=2, result=[NEED])
    sleeps = []

    out = run_extraction(
        db, "riverside", [s.messages[0].id], llm,
        max_attempts=4, base_delay=1.0, max_delay=30.0, sleep=sleeps.append, rng=lambda: 1.0,
    )

    assert out["results"][0]["status"] == "processed"
    assert len(llm.calls) == 3
    assert sleeps == [1.0, 2.0]


def test_retry_after_header_is_respected(db):
    s = _setup(db)
    llm = FlakyLLM(failures=1, result=[NEED], error=TransientLLMError("429", retry_after=7))
    sleeps = []

    run_extraction(
        db, "riverside", [s.messages[0].id], llm,
        max_attempts=3, base_delay=1.0, max_delay=30.0, sleep=sleeps.append, rng=lambda: 1.0,
    )

    assert sleeps == [7.0]


def test_transient_errors_give_up_after_max_attempts(db):
    s = _setup(db)
    llm = ScriptedLLM(default=TransientLLMError("503"))
    sleeps = []

    out = run_extraction(
        db, "riverside", [s.messages[0].id], llm,
        max_attempts=3, base_delay=1.0, max_delay=30.0, sleep=sleeps.append, rng=lambda: 1.0,
    )

    assert out["results"][0]["status"] == "failed"
    assert len(llm.calls) == 3
    assert len(sleeps) == 2
    assert _rows(db) == []


# ---------- authorization ----------


def test_member_cannot_trigger_extraction(db):
    s = _setup(db)
    llm = FakeLLMClient(canned_response=[NEED])
    _use(llm)

    resp = _post([s.messages[0].id], token="tok-member")

    assert resp.status_code == 403
    assert llm.calls == [] and _rows(db) == []


def test_admin_of_another_club_cannot_trigger_extraction(db):
    s = _setup(db)
    llm = FakeLLMClient(canned_response=[NEED])
    _use(llm)

    resp = _post([s.messages[0].id], token="tok-other-admin", club="riverside")

    assert resp.status_code == 403
    assert llm.calls == [] and _rows(db) == []


def test_message_ids_from_another_club_are_not_processed(db):
    s = _setup(db)
    llm = FakeLLMClient(canned_response=[NEED])
    _use(llm)

    resp = _post([s.foreign.id])

    assert resp.json()["results"][0]["status"] == "not_found"
    assert llm.calls == [] and _rows(db) == []


# ---------- restricted data ----------


def test_restricted_attributes_are_stored_but_excluded_from_matchable(db):
    s = _setup(db)
    _use(FakeLLMClient(canned_response=[NEED, HEALTH]))

    _post([s.messages[0].id])

    stored = _rows(db, s.messages[0].id)
    assert any(r.restricted for r in stored)  # written, flagged restricted
    visible = matchable_attributes(db, "riverside", s.member.id)
    assert [a.text for a in visible] == ["raising a seed round"]
