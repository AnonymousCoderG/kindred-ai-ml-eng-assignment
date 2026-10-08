## Bug trace: knowledge query leaks other club
[{"chunk_id":4,"club_id":"riverside","title":"Cancellation policy","body":"Riverside bookings can be cancelled up to 24 hours ahead for a full refund."},{"chunk_id":7,"club_id":"oakhurst","title":"Opening hours","body":"Oakhurst is open 6am to midnight, the pool closes at 9pm."},{"chunk_id":5,"club_id":"oakhurst","title":"Guest fees","body":"Oakhurst guest fees are $75 per visit, capped at two guests per member per month."},{"chunk_id":1,"club_id":"riverside","title":"Guest fees","body":"Riverside guest fees are $50 per visit, waived for members' immediate family."},{"chunk_id":6,"club_id":"oakhurst","title":"Dress code","body":"Oakhurst requires collared shirts in all dining areas, no exceptions."}]## Bug trace 2: oakhurst member sees riverside chunks
[{"chunk_id":4,"club_id":"riverside","title":"Cancellation policy","body":"Riverside bookings can be cancelled up to 24 hours ahead for a full refund."},{"chunk_id":7,"club_id":"oakhurst","title":"Opening hours","body":"Oakhurst is open 6am to midnight, the pool closes at 9pm."},{"chunk_id":5,"club_id":"oakhurst","title":"Guest fees","body":"Oakhurst guest fees are $75 per visit, capped at two guests per member per month."},{"chunk_id":1,"club_id":"riverside","title":"Guest fees","body":"Riverside guest fees are $50 per visit, waived for members' immediate family."},{"chunk_id":6,"club_id":"oakhurst","title":"Dress code","body":"Oakhurst requires collared shirts in all dining areas, no exceptions."}]
## Auth check (403) for contrast
HTTP/1.1 403 Forbidden
date: Thu, 08 Oct 2026 06:56:45 GMT
server: uvicorn
content-length: 38
content-type: application/json

{"detail":"not a member of this club"}## Initial test run
collected 7 items

tests\test_bookings.py .                                                 [ 14%]
tests\test_introductions.py .                                            [ 28%]
tests\test_knowledge.py ..                                               [ 57%]
tests\test_matching.py .                                                 [ 71%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 7 passed, 1 warning in 1.97s =========================
## Bug trace 4: introductions cross-club (riverside member reads oakhurst members 11 and 12)
HTTP/1.1 200 OK
date: Thu, 08 Oct 2026 07:19:10 GMT
server: uvicorn
content-length: 159
content-type: application/json

{"reason_text":"Because fractional CFO experience across three portfolio companies and recently diagnosed with a chronic condition — a good business match."}## Bug trace 5: session double charge after crash
{"status":"awaiting_confirmation","party_size":2}{"detail":"simulated crash after charge, before persistence"}{"detail":"simulated crash after charge, before persistence"}{"charges":[500,500]}{"session_id":1,"status":"active","party_size":2,"awaiting_confirmation":true,"booking_id":null}## Bug trace 6: booking 1 ($80) confirmed for 1 cent, charged twice
{"status":"succeeded","attempt_id":1,"booking_status":"confirmed"}{"status":"succeeded","attempt_id":2,"booking_status":"confirmed"}{"charges":[500,500,1,1]}## Bug trace 2: oakhurst member sees riverside chunks
[{"chunk_id":4,"club_id":"riverside","title":"Cancellation policy","body":"Riverside bookings can be cancelled up to 24 hours ahead for a full refund."},{"chunk_id":7,"club_id":"oakhurst","title":"Opening hours","body":"Oakhurst is open 6am to midnight, the pool closes at 9pm."},{"chunk_id":5,"club_id":"oakhurst","title":"Guest fees","body":"Oakhurst guest fees are $75 per visit, capped at two guests per member per month."},{"chunk_id":1,"club_id":"riverside","title":"Guest fees","body":"Riverside guest fees are $50 per visit, waived for members' immediate family."},{"chunk_id":6,"club_id":"oakhurst","title":"Dress code","body":"Oakhurst requires collared shirts in all dining areas, no exceptions."}]
## Auth check (403) for contrast
HTTP/1.1 403 Forbidden
date: Thu, 08 Oct 2026 07:23:49 GMT
server: uvicorn
content-length: 38
content-type: application/json

{"detail":"not a member of this club"}

## Initial test run

collected 7 items

tests\test_bookings.py .                                                 [ 14%]
tests\test_introductions.py .                                            [ 28%]
tests\test_knowledge.py ..                                               [ 57%]
tests\test_matching.py .                                                 [ 71%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 7 passed, 1 warning in 1.90s =========================

