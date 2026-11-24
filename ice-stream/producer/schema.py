import random
import uuid
from datetime import datetime, timezone


def generate_transaction() -> dict:
    subtotal = round(random.uniform(5, 500), 2)
    tax = round(subtotal * 0.08, 2)
    return {
        "order_id": str(uuid.uuid4()),
        "user_id": random.randint(1, 10_000),
        "tax_amount": tax,
        "total": round(subtotal + tax, 2),
        "ts": datetime.now(timezone.utc).isoformat(),
    }