"""Structured attribute extraction pipeline (Part 3).

Per message: scope to the club, skip if already processed (idempotency), call the
LLM with a retry strategy, validate the output, then write the rows.
One message failing never fails the batch.
"""

import logging
import random
import time
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.config import settings
from app.llm_client import LLMClient
from app.llm_errors import ExtractionFailed, PermanentLLMError, TransientLLMError
from app.models import ConversationMessage, MemberAttribute

log = logging.getLogger("extraction")

ADVISORY_LOCK_NAMESPACE = 4242


class ExtractedItem(BaseModel):
    """Schema every LLM item must satisfy before it is written to the database."""

    model_config = ConfigDict(str_strip_whitespace=True)

    kind: Literal["need", "offer", "context", "interest"]
    text: str = Field(min_length=1, max_length=300)
    confidence: float = Field(ge=0.0, le=1.0)
    restricted: bool


def validate_items(raw: object) -> tuple[list[ExtractedItem], int]:
    """Keep valid items, drop malformed ones. Returns (valid_items, dropped_count)."""
    if not isinstance(raw, list):
        raise PermanentLLMError("LLM output was not a list")
    valid: list[ExtractedItem] = []
    dropped = 0
    for item in raw:
        try:
            valid.append(ExtractedItem.model_validate(item))
        except ValidationError:
            dropped += 1
    return valid, dropped


def extract_with_retry(
    llm: LLMClient,
    message_text: str,
    *,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    sleep: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = random.random,
) -> tuple[list[ExtractedItem], int]:
    """Call the LLM and validate the result, using the retry strategy below.

    Retry strategy: only TransientLLMError (429 rate limit, 5xx, timeout, network)
    is retried, up to max_attempts. The wait is exponential backoff
    (base_delay * 2 ** (attempt - 1), capped at max_delay) with jitter between 50%
    and 100% of that value, and never shorter than a Retry-After header the
    provider sent. PermanentLLMError (400, 401, unparseable output) is raised at
    once, because repeating the same request cannot succeed.
    """
    max_attempts = max_attempts or settings.llm_max_attempts
    base_delay = settings.llm_base_delay_seconds if base_delay is None else base_delay
    max_delay = settings.llm_max_delay_seconds if max_delay is None else max_delay

    last_error: TransientLLMError | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return validate_items(llm.extract_attributes(message_text))
        except TransientLLMError as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            delay = min(max_delay, base_delay * 2 ** (attempt - 1)) * (0.5 + 0.5 * rng())
            if exc.retry_after is not None:
                delay = max(delay, min(exc.retry_after, max_delay))
            log.warning("LLM attempt %d/%d failed (%s); retrying in %.1fs", attempt, max_attempts, exc, delay)
            sleep(delay)
    raise ExtractionFailed(f"gave up after {max_attempts} attempts: {last_error}")


def _already_processed(db: Session, message: ConversationMessage) -> bool:
    # IDEMPOTENCY KEY: a message counts as processed when a member_attributes row
    # exists with (club_id, source_message_id) == (message.club_id, message.id).
    return (
        db.query(MemberAttribute.id)
        .filter(
            MemberAttribute.club_id == message.club_id,
            MemberAttribute.source_message_id == message.id,
        )
        .first()
        is not None
    )


def _process_message(db: Session, club_id: str, message_id: int, llm: LLMClient, retry_kwargs: dict) -> dict:
    # Scoped to the club: an id that belongs to another club looks like a missing one.
    message = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.id == message_id, ConversationMessage.club_id == club_id)
        .first()
    )
    if message is None:
        return {"message_id": message_id, "status": "not_found"}

    if _already_processed(db, message):
        return {"message_id": message_id, "status": "skipped_already_processed"}

    items, dropped = extract_with_retry(llm, message.body, **retry_kwargs)

    # Serialise concurrent runs on the same message, then re-check. The table has no
    # unique constraint (no schema changes allowed), so this lock plus the re-check
    # is what stops two simultaneous requests from both inserting.
    db.execute(sql_text("SELECT pg_advisory_xact_lock(:ns, :mid)"), {"ns": ADVISORY_LOCK_NAMESPACE, "mid": message.id})
    if _already_processed(db, message):
        db.rollback()
        return {"message_id": message_id, "status": "skipped_already_processed"}

    seen: set[tuple[str, str]] = set()
    rows = []
    for item in items:
        key = (item.kind, " ".join(item.text.lower().split()))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            MemberAttribute(
                member_id=message.member_id,
                club_id=message.club_id,
                kind=item.kind,
                text=item.text,
                confidence=item.confidence,
                restricted=item.restricted,
                source_message_id=message.id,
            )
        )
    db.add_all(rows)
    db.commit()  # all of a message's rows commit together, or none do
    return {
        "message_id": message_id,
        "status": "processed",
        "attributes_created": len(rows),
        "attributes_dropped": dropped,
    }


def run_extraction(
    db: Session,
    club_id: str,
    message_ids: list[int],
    llm: LLMClient,
    *,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    sleep: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = random.random,
) -> dict:
    retry_kwargs = dict(max_attempts=max_attempts, base_delay=base_delay, max_delay=max_delay, sleep=sleep, rng=rng)
    results = []
    for message_id in dict.fromkeys(message_ids):  # de-duplicate, keep order
        try:
            results.append(_process_message(db, club_id, message_id, llm, retry_kwargs))
        except Exception as exc:  # one message failing must not fail the batch
            db.rollback()
            log.error("extraction failed for message %s: %s", message_id, exc)
            results.append(
                {"message_id": message_id, "status": "failed", "reason": f"{type(exc).__name__}: {str(exc)[:200]}"}
            )

    summary = {
        "processed": sum(r["status"] == "processed" for r in results),
        "skipped_already_processed": sum(r["status"] == "skipped_already_processed" for r in results),
        "failed": sum(r["status"] == "failed" for r in results),
        "not_found": sum(r["status"] == "not_found" for r in results),
        "attributes_created": sum(r.get("attributes_created", 0) for r in results),
    }
    return {"club_id": club_id, "summary": summary, "results": results}
