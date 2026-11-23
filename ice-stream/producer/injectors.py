import random

NULLABLE_FIELDS = ["tax_amount", "user_id", "total"]


def inject_nulls(event: dict, rate: float) -> dict:
    """With probability `rate`, set one random field to None."""
    if random.random() < rate:
        event[random.choice(NULLABLE_FIELDS)] = None
    return event


def inject_drift(event: dict, rate: float) -> dict:
    """With probability `rate`, rename a column, add a column, or change a type."""
    if random.random() >= rate:
        return event
    mode = random.choice(["rename", "add", "type"])
    if mode == "rename" and "tax_amount" in event:
        event["tax"] = event.pop("tax_amount")
    elif mode == "add":
        event["coupon_code"] = random.choice(["SAVE10", "WELCOME", "FREESHIP"])
    elif mode == "type" and event.get("total") is not None:
        event["total"] = str(event["total"])
    return event