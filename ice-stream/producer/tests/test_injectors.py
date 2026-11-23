from schema import generate_transaction
from injectors import inject_nulls, inject_drift


def test_no_nulls_when_rate_zero():
    event = inject_nulls(generate_transaction(), 0.0)
    assert None not in event.values()


def test_always_null_when_rate_one():
    event = inject_nulls(generate_transaction(), 1.0)
    assert None in event.values()


def test_no_drift_when_rate_zero():
    original = generate_transaction()
    assert inject_drift(dict(original), 0.0) == original


def test_drift_changes_event_when_rate_one():
    original = generate_transaction()
    assert inject_drift(dict(original), 1.0) != original