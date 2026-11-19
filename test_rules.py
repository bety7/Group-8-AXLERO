from app.rules import validate_event

def valid():
    return {"event_id":"e1","order_id":"o1","event_time":"2026-01-01T00:00:00Z",
            "amount":12.5,"currency":"INR","customer_id":"c1"}

def test_valid_event_passes():
    ok, errors = validate_event(valid())
    assert ok and errors == []

def test_null_amount_fails():
    event = valid()
    event["amount"] = None
    ok, errors = validate_event(event)
    assert not ok and any("NULL_AMOUNT" in e for e in errors)

def test_negative_amount_fails():
    event = valid()
    event["amount"] = -1
    ok, errors = validate_event(event)
    assert not ok and any("INVALID_AMOUNT" in e for e in errors)

def test_schema_drift_fails():
    event = valid()
    del event["customer_id"]
    ok, errors = validate_event(event)
    assert not ok and any("SCHEMA_DRIFT" in e for e in errors)
