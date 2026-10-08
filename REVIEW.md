# Code Review

Issues are ordered by business impact. All traces below are literal requests and responses from my own running instance (seeded data, API on localhost:8000).

Baseline: the 7 starter tests pass (`7 passed`), but none of them tests cross-club access, so they pass even though issues 1 and 2 are live.

---

## 1. Knowledge query returns other clubs' documents

- **File / line:** `app/routers/knowledge.py:28-33` (guard at line 19)
- **Category:** Data Isolation
- **Severity:** Critical
- **Description:** The guard at line 19 only checks that the caller's club equals the `club_id` in the URL. The similarity search at lines 28-33 has no `club_id` filter, so it ranks every club's chunks together and returns the top 5. An authorised caller therefore receives other clubs' private documents, and can also lose some of their own club's documents to the other club's.
- **Recommended fix:** Add `.filter(KnowledgeChunk.club_id == club_id)` before `order_by`, and add tests that assert every returned chunk belongs to the caller's club.

**Trace**

Request:
```
curl -H "X-Member-Token: riverside-admin" "http://localhost:8000/clubs/riverside/knowledge/query?q=parking"
```
Response (chunks 7, 5 and 6 belong to `oakhurst`):
```
[{"chunk_id":4,"club_id":"riverside","title":"Cancellation policy","body":"Riverside bookings can be cancelled up to 24 hours ahead for a full refund."},{"chunk_id":7,"club_id":"oakhurst","title":"Opening hours","body":"Oakhurst is open 6am to midnight, the pool closes at 9pm."},{"chunk_id":5,"club_id":"oakhurst","title":"Guest fees","body":"Oakhurst guest fees are $75 per visit, capped at two guests per member per month."},{"chunk_id":1,"club_id":"riverside","title":"Guest fees","body":"Riverside guest fees are $50 per visit, waived for members' immediate family."},{"chunk_id":6,"club_id":"oakhurst","title":"Dress code","body":"Oakhurst requires collared shirts in all dining areas, no exceptions."}]
```

Contrast, the existing guard does work for a direct cross-club URL, which is why it does not catch this bug (it checks the request, not the rows returned):
```
curl -i -H "X-Member-Token: riverside-member-1" "http://localhost:8000/clubs/oakhurst/knowledge/query?q=parking"
HTTP/1.1 403 Forbidden
{"detail":"not a member of this club"}
```

---

## 2. Introductions expose any member's attributes, including restricted health data

- **File / line:** `app/routers/introductions.py:19-20`
- **Category:** Data Isolation
- **Severity:** Critical
- **Description:** Attributes are fetched by `member_id` only. There is no check that either member belongs to the caller's club, and no filter on `restricted`, so a member of one club can request two members of another club and read their private attributes, including a health detail.
- **Recommended fix:** Load both members scoped to the caller's club (return 404, not 403, so the response does not confirm a member exists elsewhere), and read attributes through one function that excludes `restricted` rows.

**Trace**

Request (a riverside member asks about oakhurst members 11 and 12):
```
curl -i -H "X-Member-Token: riverside-member-1" "http://localhost:8000/introductions/11/12?reason=business"
```
Response:
```
HTTP/1.1 200 OK
content-type: application/json

{"reason_text":"Because fractional CFO experience across three portfolio companies and recently diagnosed with a chronic condition — a good business match."}
```
Member 12's attribute "recently diagnosed with a chronic condition" is stored with `restricted = true`.

---

## 3. Session confirmation charges before persisting; a crash or retry double-charges

- **File / line:** `app/services/session_flow.py:31-55` (charge at line 36, simulated crash at lines 38-39)
- **Category:** Data Integrity
- **Severity:** High
- **Description:** The `affirm` branch calls the payment provider at line 36 before anything is saved, and its only guard is `awaiting_confirmation`, which is not cleared until line 53. A crash between the charge and the commit, or a client retry, charges the member again while the session still looks unpaid. The code's own comment at lines 34-35 notes there is no prior-charge check.
- **Recommended fix:** Create the booking and a `PaymentAttempt` carrying an idempotency key (derived from the session id) and commit it before charging; on a retry, look up the existing attempt and reuse its result instead of charging again.

**Trace**

Requests (session 1, `riverside-member-1`):
```
POST /sessions/1/turn  {"intent":"book","party_size":2}
POST /sessions/1/turn  {"intent":"affirm","amount_cents":500,"simulate_crash":true}
POST /sessions/1/turn  {"intent":"affirm","amount_cents":500,"simulate_crash":true}
GET  /sessions/debug/payment-charge-log   (riverside-admin)
GET  /sessions/1
```
Responses:
```
{"status":"awaiting_confirmation","party_size":2}
{"detail":"simulated crash after charge, before persistence"}
{"detail":"simulated crash after charge, before persistence"}
{"charges":[500,500]}
{"session_id":1,"status":"active","party_size":2,"awaiting_confirmation":true,"booking_id":null}
```
Two real charges were made, and the session shows no booking.

---

## 4. A refund_dispute escalation can be overridden and charged

- **File / line:** `app/services/session_flow.py:14-17`, `:31`, `:52`
- **Category:** Data Integrity
- **Severity:** High
- **Description:** `refund_dispute` sets the status to `escalated` but leaves `awaiting_confirmation` true. A following `affirm` passes the check at line 31, charges the member, and line 52 overwrites the status with `confirmed`. A dispute that is meant to always escalate is auto-resolved.
- **Recommended fix:** Only allow `affirm` while `session.status == "active"`, and clear `awaiting_confirmation` when escalating.

**Trace**

Requests (session 2, `riverside-member-1`; `/sessions/2/turn` for each):
```
POST /sessions/1/turn  {"intent":"book","party_size":2}
POST /sessions/1/turn  {"intent":"refund_dispute"}
POST /sessions/1/turn  {"intent":"affirm","amount_cents":500}
```
Responses:
```
{"status":"awaiting_confirmation","party_size":2}
{"status":"escalated"}
{"status":"confirmed","booking_id":4}
```

---

## 5. confirm-payment trusts the client's amount and can charge repeatedly

- **File / line:** `app/routers/bookings.py:20-41` (amount used at line 29)
- **Category:** Data Integrity
- **Severity:** High
- **Description:** The charge amount comes from the request body, not from the booking, and the booking's current status is never checked. An $80.00 booking (8000 cents) was confirmed by a 1-cent charge and then charged again. `PaymentAttempt.idempotency_key` exists (`app/models.py:96`) but is never used. The provider is also charged (line 29) before the attempt is recorded (lines 33-41), so a failure in between leaves a charge with no record.
- **Recommended fix:** Charge `booking.amount_cents` (ignore or validate the client value), reject bookings that are already confirmed, and record the attempt with an idempotency key before calling the provider.

**Trace**

Requests (booking 1, owned by `riverside-member-1`, `amount_cents` 8000):
```
POST /bookings/1/confirm-payment  {"amount_cents":1}
POST /bookings/1/confirm-payment  {"amount_cents":1}
```
Responses:
```
{"status":"succeeded","attempt_id":1,"booking_status":"confirmed"}
{"status":"succeeded","attempt_id":2,"booking_status":"confirmed"}
```

---

## 6. Payment charge log is global across clubs

- **File / line:** `app/routers/sessions.py:13-18`, `app/services/payment_mock.py:20`, `app/auth.py:18-21`
- **Category:** Data Isolation
- **Severity:** Medium
- **Description:** `require_admin` only checks the role, and the log is one global list of amounts with no club or booking attached. After riverside's charges, the oakhurst admin read them.
- **Recommended fix:** Record club and booking with each charge, and filter the log by the calling admin's club.

**Trace**

Request:
```
curl -s -H "X-Member-Token: oakhurst-admin" http://localhost:8000/sessions/debug/payment-charge-log
```
Response (all four charges were made by riverside members):
```
{"charges":[500,500,1,1]}
```

---

## 7. Restricted attributes feed the matching profile

- **File / line:** `app/services/matching_service.py:10-12` (and the seeded embeddings built at `scripts/seed.py:193-194`)
- **Category:** Data Isolation
- **Severity:** Medium
- **Description:** `build_member_profile_text` joins every attribute regardless of `restricted`, and the stored profile embeddings were built that way, so health and anxiety text influences who gets suggested as a match.
- **Recommended fix:** Build the profile text from non-restricted attributes only, and recompute the embedding when ranking.
- **Status:** Fixed in Part 3 (`app/scoping.py` `_matchable`, `matching_service.py`); tests in `tests/test_matching_restricted.py`.

**Trace**

Request (BEFORE the fix, a riverside member asks for candidates; the ranking is computed from stored profile embeddings that include restricted text):
```
curl -H "X-Member-Token: riverside-member-1" "http://localhost:8000/members/3/candidates?reason=business"
```
Response: ranked list including member 5, whose only attribute is restricted (see `TERMINAL_LOG.md`, "matching BEFORE fix"). After the fix the ranking is computed from non-restricted text only (see "matching AFTER fix"); `test_matching_restricted.py` asserts the embedder never receives restricted text.

---

## 8. Repeated queries and embedding inside the ranking loop

- **File / line:** `app/services/matching_service.py:32-35`
- **Category:** Performance
- **Severity:** Low
- **Description:** The requesting member's attributes are queried and embedded again for every candidate inside the loop, instead of once before it.
- **Recommended fix:** Compute the query vector once before the loop.
- **Status:** Fixed in Part 3 (requester embedded once).
- **Evidence:** No request trace; found by reading the code (`matching_service.py:32-35`).
