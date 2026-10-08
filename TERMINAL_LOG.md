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



## Bug trace 7: refund_dispute escalation bypassed (session 2)

{"status":"awaiting_confirmation","party_size":2}
{"status":"escalated"}
{"status":"confirmed","booking_id":4}


## Part 2: BEFORE fix, new isolation tests fail

        resp = client.get(
            f"/introductions/{r1.id}/{r2.id}",
            params={"reason": "business"},
            headers={"X-Member-Token": "tok-r1"},
        )
        assert resp.status_code == 200
        text = resp.json()["reason_text"]
        assert "CFO" in text  # same-club introductions still work
>       assert "chronic condition" not in text  # restricted data never leaks
E       AssertionError: assert 'chronic condition' not in 'Because nee...iness match.'
E         
E         'chronic condition' is contained here:
E           Because needs a CFO and has a chronic condition; offers CFO services � a good business match.
E         ?                               +++++++++++++++++

tests\test_club_isolation.py:124: AssertionError
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/test_club_isolation.py::test_knowledge_query_only_returns_own_club_chunks[riverside]
FAILED tests/test_club_isolation.py::test_knowledge_query_only_returns_own_club_chunks[oakhurst]
FAILED tests/test_club_isolation.py::test_introduction_rejects_two_members_of_another_club
FAILED tests/test_club_isolation.py::test_introduction_rejects_when_only_one_member_is_foreign
FAILED tests/test_club_isolation.py::test_introduction_unknown_member_is_404
FAILED tests/test_club_isolation.py::test_introduction_never_includes_restricted_attributes
======================== 6 failed, 1 warning in 2.64s =========================



## Part 2: AFTER fix, all tests

platform win32 -- Python 3.13.13, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main
configfile: pytest.ini
plugins: anyio-4.15.1
collected 13 items

tests\test_bookings.py .                                                 [  7%]
tests\test_club_isolation.py ......                                      [ 53%]
tests\test_introductions.py .                                            [ 61%]
tests\test_knowledge.py ..                                               [ 76%]
tests\test_matching.py .                                                 [ 84%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 13 passed, 1 warning in 3.93s ========================



## Part 2: AFTER fix trace 1, knowledge query as riverside-admin

[{"chunk_id":4,"club_id":"riverside","title":"Cancellation policy","body":"Riverside bookings can be cancelled up to 24 hours ahead for a full refund."},{"chunk_id":1,"club_id":"riverside","title":"Guest fees","body":"Riverside guest fees are $50 per visit, waived for members' immediate family."},{"chunk_id":2,"club_id":"riverside","title":"Dress code","body":"Riverside's dress code is smart casual after 6pm, resort wear during the day."},{"chunk_id":3,"club_id":"riverside","title":"Opening hours","body":"Riverside is open 7am to 11pm daily, kitchen closes at 10pm."}]


## Part 2: AFTER fix trace 2, introductions across clubs

HTTP/1.1 404 Not Found
date: Thu, 08 Oct 2026 07:36:04 GMT
server: uvicorn
content-length: 29
content-type: application/json

{"detail":"member not found"}


## Part 2: AFTER fix trace 3, same-club introduction still works and hides restricted data

HTTP/1.1 200 OK
date: Thu, 08 Oct 2026 07:36:19 GMT
server: uvicorn
content-length: 141
content-type: application/json

{"reason_text":"Because raising a seed round, looking for angel investors; might be raising again next year and  — a good business match."}


## Part 3: batch run 1, real API calls




## Part 3: batch run 2, same batch, proves idempotency




## Part 3: rows written

 msg | kind | restricted | confidence | text 
-----+------+------------+------------+------
(0 rows)




## Part 3: tests with LLM test double

============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main
configfile: pytest.ini
plugins: anyio-4.15.1
collected 13 items

tests\test_bookings.py .                                                 [  7%]
tests\test_club_isolation.py ......                                      [ 53%]
tests\test_introductions.py .                                            [ 61%]
tests\test_knowledge.py ..                                               [ 76%]
tests\test_matching.py .                                                 [ 84%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 13 passed, 1 warning in 8.94s ========================



## Part 3: tests with LLM test double

============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main
configfile: pytest.ini
plugins: anyio-4.15.1
collected 24 items

tests\test_bookings.py .                                                 [  4%]
tests\test_club_isolation.py ......                                      [ 29%]
tests\test_extraction.py ...........                                     [ 75%]
tests\test_introductions.py .                                            [ 79%]
tests\test_knowledge.py ..                                               [ 87%]
tests\test_matching.py .                                                 [ 91%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 24 passed, 1 warning in 11.41s ========================



## Part 3: tests with LLM test double

============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main
configfile: pytest.ini
plugins: anyio-4.15.1
collected 24 items

tests\test_bookings.py .                                                 [  4%]
tests\test_club_isolation.py ......                                      [ 29%]
tests\test_extraction.py ...........                                     [ 75%]
tests\test_introductions.py .                                            [ 79%]
tests\test_knowledge.py ..                                               [ 87%]
tests\test_matching.py .                                                 [ 91%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 24 passed, 1 warning in 9.55s ========================



## Part 3: batch run 1, real API calls

{
    "club_id": "riverside",
    "summary": {
        "processed": 1,
        "skipped_already_processed": 0,
        "failed": 4,
        "not_found": 0,
        "attributes_created": 2
    },
    "results": [
        {
            "message_id": 10,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 11,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 12,
            "status": "processed",
            "attributes_created": 2,
            "attributes_dropped": 0
        },
        {
            "message_id": 13,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        }
    ]
}



## Part 3: rows written after batch run 1

 msg |  kind   | restricted | confidence |                 text                  
-----+---------+------------+------------+---------------------------------------
  12 | context | t          |          1 | ADHD diagnosis
  12 | context | f          |        0.9 | plans everything in a strict calendar
(2 rows)




## Part 3: batch run 2, same batch (message 12 skipped, failed ones retried)

{
    "club_id": "riverside",
    "summary": {
        "processed": 0,
        "skipped_already_processed": 1,
        "failed": 4,
        "not_found": 0,
        "attributes_created": 0
    },
    "results": [
        {
            "message_id": 10,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 11,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 2,
        "skipped_already_processed": 1,
        "failed": 2,
        "not_found": 0,
        "attributes_created": 3
    },
    "results": [
        {
            "message_id": 10,
            "status": "processed",
            "attributes_created": 1,
            "attributes_dropped": 0
        },
        {
            "message_id": 11,
            "status": "processed",
            "attributes_created": 2,
            "attributes_dropped": 0
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 0,
        "skipped_already_processed": 3,
        "failed": 2,
        "not_found": 0,
        "attributes_created": 0
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 0,
        "skipped_already_processed": 3,
        "failed": 2,
        "not_found": 0,
        "attributes_created": 0
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 0,
        "skipped_already_processed": 3,
        "failed": 2,
        "not_found": 0,
        "attributes_created": 0
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 0,
        "skipped_already_processed": 3,
        "failed": 2,
        "not_found": 0,
        "attributes_created": 0
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstre"
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 1,
        "skipped_already_processed": 3,
        "failed": 1,
        "not_found": 0,
        "attributes_created": 2
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "processed",
            "attributes_created": 2,
            "attributes_dropped": 0
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-31b-it:free is temporarily rate-limited upstream. "
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 0,
        "skipped_already_processed": 4,
        "failed": 1,
        "not_found": 0,
        "attributes_created": 0
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 14,
            "status": "failed",
            "reason": "ExtractionFailed: gave up after 5 attempts: rate limited or timed out (429): {\"error\":{\"message\":\"Provider returned error\",\"code\":429,\"metadata\":{\"raw\":\"google/gemma-4-31b-it:free is temporarily rate-limited upstream. "
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 1,
        "skipped_already_processed": 4,
        "failed": 0,
        "not_found": 0,
        "attributes_created": 2
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 14,
            "status": "processed",
            "attributes_created": 2,
            "attributes_dropped": 0
        }
    ]
}

{
    "club_id": "riverside",
    "summary": {
        "processed": 0,
        "skipped_already_processed": 5,
        "failed": 0,
        "not_found": 0,
        "attributes_created": 0
    },
    "results": [
        {
            "message_id": 10,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 11,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 12,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 13,
            "status": "skipped_already_processed"
        },
        {
            "message_id": 14,
            "status": "skipped_already_processed"
        }
    ]
}



## Part 3: rows written

 msg |   kind   | restricted | confidence |                             text                             
-----+----------+------------+------------+--------------------------------------------------------------
  12 | context  | t          |          1 | ADHD diagnosis
  12 | context  | f          |        0.9 | plans everything in a strict calendar
  10 | need     | f          |          1 | co-founder with a strong operations background for a logisti
  11 | offer    | f          |          1 | mentor anyone getting started with angel investing
  11 | context  | f          |          1 | available on Thursdays
  13 | interest | f          |        0.9 | trail running
  13 | need     | f          |        0.9 | Sunday morning running group
  14 | context  | t          |        0.9 | therapist suggested attending more small gatherings
  14 | interest | f          |        0.8 | attending small gatherings
(9 rows)




## Part 3: eval run (real API)
Note: this ran during a provider 429 outage. The eval scored it 0/12 until I changed it to report INCONCLUSIVE (exit code 2) for outages. See .ai-conversations/05-eval-and-outage-handling.md.

LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 0.7s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.9s


## Part 3: eval run (real API)

LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 0.5s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.2s
LLM attempt 3/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 3.0s
LLM attempt 4/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 4.8s
LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 0.5s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.9s
LLM attempt 3/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 2.6s
LLM attempt 4/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 6.9s
LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 0.8s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.8s
LLM attempt 3/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 2.9s
LLM attempt 4/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 6.0s
LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 0.7s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.5s
LLM attempt 3/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 3.1s
LLM attempt 4/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 5.3s
  (record 1: extraction failed: gave up after 5 attempts: rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you)
[FAIL] record 1: kind WRONG (expected need), restricted WRONG (expected False), keywords MISSING (expected one of ['series a', 'vc'])
        got: no attribute extracted
        message: I'm trying to raise a Series A in the next few months, would love intros to VCs.
  (record 2: extraction failed: gave up after 5 attempts: rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you)
[FAIL] record 2: kind WRONG (expected offer), restricted WRONG (expected False), keywords MISSING (expected one of ['series a', 'fundrais'])
        got: no attribute extracted
        message: I've led fundraising for three Series A rounds as an operator, happy to help others through it.
  (record 3: extraction failed: gave up after 5 attempts: rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you)
[FAIL] record 3: kind WRONG (expected context), restricted WRONG (expected True), keywords MISSING (expected one of ['therapy'])
        got: no attribute extracted
        message: I've been in therapy for the last year and it's helped a lot, just so you understand where I'm at.
  (record 4: extraction failed: gave up after 5 attempts: rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you)
[FAIL] record 4: kind WRONG (expected interest), restricted WRONG (expected False), keywords MISSING (expected one of ['running'])
        got: no attribute extracted
        message: Does anyone want to join a weekly running club on Tuesday mornings?

Overall score: 0/12 = 0.00%   (threshold 90%)
Restricted-flag errors: 4
EVAL FAILED

LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.0s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.7s
LLM attempt 3/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 2.2s
LLM attempt 4/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 4.2s
LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 0.8s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.7s
LLM attempt 3/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 3.4s
LLM attempt 4/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 6.9s
LLM attempt 1/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.0s
LLM attempt 2/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 1.9s
LLM attempt 3/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 3.0s
LLM attempt 4/5 failed (rate limited or timed out (429): {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"google/gemma-4-31b-it:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate you); retrying in 4.9s


## Part 3: eval run (real API, nemotron-3-super)

[PASS] record 1: kind ok (expected need), restricted ok (expected False), keywords ok (expected one of ['series a', 'vc'])
        got: kind=need restricted=False text="raising a Series A, looking for VC introductions"
        message: I'm trying to raise a Series A in the next few months, would love intros to VCs.
[PASS] record 2: kind ok (expected offer), restricted ok (expected False), keywords ok (expected one of ['series a', 'fundrais'])
        got: kind=offer restricted=False text="led fundraising for three Series A rounds as an operator, happy to help others through it"
        message: I've led fundraising for three Series A rounds as an operator, happy to help others through it.
[PASS] record 3: kind ok (expected context), restricted ok (expected True), keywords ok (expected one of ['therapy'])
        got: kind=context restricted=True text="been in therapy for the last year, finds it helpful"
        message: I've been in therapy for the last year and it's helped a lot, just so you understand where I'm at.
[PASS] record 4: kind ok (expected interest), restricted ok (expected False), keywords ok (expected one of ['running'])
        got: kind=interest restricted=False text="looking for participants for a weekly running club on Tuesday mornings"
        message: Does anyone want to join a weekly running club on Tuesday mornings?

Overall score: 12/12 = 100.00%   (threshold 90%)
Restricted-flag errors: 0
EVAL PASSED



## Part 3: matching BEFORE fix (member 5 has only a restricted attribute)

[
    {
        "member_id": 4,
        "name": "Riverside Member 2",
        "score": 0.0
    },
    {
        "member_id": 7,
        "name": "Riverside Member 5",
        "score": 0.0
    },
    {
        "member_id": 8,
        "name": "Riverside Member 6",
        "score": 0.0
    },
    {
        "member_id": 6,
        "name": "Riverside Member 4",
        "score": -0.1213
    },
    {
        "member_id": 5,
        "name": "Riverside Member 3",
        "score": -0.2425
    }
]



## Part 3: matching BEFORE fix (member 5 has only a restricted attribute)

[
    {
        "member_id": 4,
        "name": "Riverside Member 2",
        "score": 0.0
    },
    {
        "member_id": 7,
        "name": "Riverside Member 5",
        "score": 0.0
    },
    {
        "member_id": 8,
        "name": "Riverside Member 6",
        "score": 0.0
    },
    {
        "member_id": 6,
        "name": "Riverside Member 4",
        "score": -0.1213
    },
    {
        "member_id": 5,
        "name": "Riverside Member 3",
        "score": -0.2425
    }
]

[{"chunk_id":4,"club_id":"riverside","title":"Cancellation policy","body":"Riverside bookings can be cancelled up to 24 hours ahead for a full refund."},{"chunk_id":1,"club_id":"riverside","title":"Guest fees","body":"Riverside guest fees are $50 per visit, waived for members' immediate family."},{"chunk_id":2,"club_id":"riverside","title":"Dress code","body":"Riverside's dress code is smart casual after 6pm, resort wear during the day."},{"chunk_id":3,"club_id":"riverside","title":"Opening hours","body":"Riverside is open 7am to 11pm daily, kitchen closes at 10pm."}][{"chunk_id":5,"club_id":"oakhurst","title":"Guest fees","body":"Oakhurst guest fees are $75 per visit, capped at two guests per member per month."},{"chunk_id":7,"club_id":"oakhurst","title":"Opening hours","body":"Oakhurst is open 6am to midnight, the pool closes at 9pm."},{"chunk_id":6,"club_id":"oakhurst","title":"Dress code","body":"Oakhurst requires collared shirts in all dining areas, no exceptions."},{"chunk_id":8,"club_id":"oakhurst","title":"Cancellation policy","body":"Oakhurst bookings are non-refundable within 48 hours of the reservation."}]
## Auth check (403) for contrast
HTTP/1.1 403 Forbidden
date: Thu, 08 Oct 2026 10:00:11 GMT
server: uvicorn
content-length: 38
content-type: application/json

{"detail":"not a member of this club"}

## Part 3: tests after matching fix

============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main
configfile: pytest.ini
plugins: anyio-4.15.1
collected 26 items

tests\test_bookings.py .                                                 [  3%]
tests\test_club_isolation.py ......                                      [ 26%]
tests\test_extraction.py ...........                                     [ 69%]
tests\test_introductions.py .                                            [ 73%]
tests\test_knowledge.py ..                                               [ 80%]
tests\test_matching.py .                                                 [ 84%]
tests\test_matching_restricted.py ..                                     [ 92%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 26 passed, 1 warning in 10.07s ========================



## Part 3: matching AFTER fix
Note: member 5 still appears because extraction (message 14) later gave that member a non-restricted attribute; the restricted text is excluded from ranking. tests/test_matching_restricted.py asserts the embedder never receives restricted text.

[
    {
        "member_id": 7,
        "name": "Riverside Member 5",
        "score": 0.297
    },
    {
        "member_id": 8,
        "name": "Riverside Member 6",
        "score": 0.2925
    },
    {
        "member_id": 6,
        "name": "Riverside Member 4",
        "score": 0.2858
    },
    {
        "member_id": 5,
        "name": "Riverside Member 3",
        "score": 0.14
    },
    {
        "member_id": 4,
        "name": "Riverside Member 2",
        "score": -0.0379
    }
]



## Part 3: tests after matching fix

============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main
configfile: pytest.ini
plugins: anyio-4.15.1
collected 26 items

tests\test_bookings.py .                                                 [  3%]
tests\test_club_isolation.py ......                                      [ 26%]
tests\test_extraction.py ...........                                     [ 69%]
tests\test_introductions.py .                                            [ 73%]
tests\test_knowledge.py ..                                               [ 80%]
tests\test_matching.py .                                                 [ 84%]
tests\test_matching_restricted.py ..                                     [ 92%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 26 passed, 1 warning in 9.39s ========================



## Part 3: tests after matching fix

============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main
configfile: pytest.ini
plugins: anyio-4.15.1
collected 26 items

tests\test_bookings.py .                                                 [  3%]
tests\test_club_isolation.py ......                                      [ 26%]
tests\test_extraction.py ...........                                     [ 69%]
tests\test_introductions.py .                                            [ 73%]
tests\test_knowledge.py ..                                               [ 80%]
tests\test_matching.py .                                                 [ 84%]
tests\test_matching_restricted.py ..                                     [ 92%]
tests\test_sessions.py ..                                                [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:40
  C:\Users\Hp\Downloads\attachai-ai-ml-eng-main\attachai-ai-ml-eng-main\.venv\Lib\site-packages\starlette\testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 26 passed, 1 warning in 11.72s ========================

