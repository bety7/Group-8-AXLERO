from datetime import datetime, timezone

REQUIRED_FIELDS = {"event_id", "order_id", "event_time", "amount", "currency", "customer_id"}

def validate_event(event: dict) -> tuple[bool, list[str]]:
    errors = []
    missing = REQUIRED_FIELDS - set(event.keys())
    if missing:
        errors.append("SCHEMA_DRIFT: missing fields " + ", ".join(sorted(missing)))
    if event.get("amount") is None:
        errors.append("NULL_AMOUNT: amount must not be null")
    else:
        try:
            if float(event["amount"]) < 0:
                errors.append("INVALID_AMOUNT: amount cannot be negative")
        except (TypeError, ValueError):
            errors.append("INVALID_AMOUNT: amount must be numeric")
    if not event.get("order_id"):
        errors.append("NULL_ORDER_ID: order_id must not be empty")
    return len(errors) == 0, errors

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
