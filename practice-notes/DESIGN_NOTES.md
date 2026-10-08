# Design Notes

## Part 2: session-flow issue

In `advance_turn` (`app/services/session_flow.py:31-55`), the `affirm` branch calls `payment_mock_client.charge` at line 36 before anything is persisted, and its only guard is `session.awaiting_confirmation`, which is not cleared until line 53. A crash between lines 36 and 54, or a client retry, therefore charges the member again while the session still looks unpaid (my trace showed `charges: [500, 500]` with `booking_id: null`). I would create the `Booking` and a `PaymentAttempt` carrying an `idempotency_key` derived from the session id, commit that before calling the provider, look up an existing attempt on retry instead of charging again, and only allow `affirm` while `session.status == "active"` so an escalated `refund_dispute` can never be charged.
