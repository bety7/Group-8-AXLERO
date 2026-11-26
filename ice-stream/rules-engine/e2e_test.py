"""End-to-end test: bad data -> breaker trips -> DLQ -> breaker resumes.

Needs running: the Docker stack and `python guard.py` (in another terminal).
Run: python e2e_test.py
"""
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from confluent_kafka import Consumer, Producer
from rules import load_rules

BOOTSTRAP = "localhost:9092"


def make_event(bad=False):
    subtotal = round(random.uniform(5, 500), 2)
    tax = round(subtotal * 0.08, 2)
    e = {"order_id": str(uuid.uuid4()), "user_id": random.randint(1, 10_000),
         "tax_amount": tax, "total": round(subtotal + tax, 2),
         "ts": datetime.now(timezone.utc).isoformat()}
    if bad:
        e["tax_amount"] = None
    return e


def main():
    cooldown = load_rules()["breaker"]["cooldown_seconds"]
    consumer = Consumer({"bootstrap.servers": BOOTSTRAP, "group.id": f"e2e-{uuid.uuid4()}",
                         "auto.offset.reset": "latest"})
    consumer.subscribe(["breaker-events", "checkout-dlq"])
    for _ in range(6):          # let the consumer get its partitions before we send data
        consumer.poll(0.5)
    producer = Producer({"bootstrap.servers": BOOTSTRAP})

    seen = {"open": False, "dlq": False, "closed": False}

    def poll_for(seconds):
        end = time.time() + seconds
        while time.time() < end:
            msg = consumer.poll(0.5)
            if msg is None or msg.error():
                continue
            if msg.topic() == "checkout-dlq":
                seen["dlq"] = True
            else:
                ev = json.loads(msg.value())
                if ev.get("to") == "OPEN":
                    seen["open"] = True
                if ev.get("to") == "CLOSED":
                    seen["closed"] = True

    print("1) Sending 300 events, 20% bad ...")
    for _ in range(300):
        producer.produce("checkout-events", json.dumps(make_event(random.random() < 0.2)).encode())
    producer.flush()
    poll_for(10)
    print("   breaker opened:", seen["open"], "| records in DLQ:", seen["dlq"])

    print(f"2) Waiting {cooldown + 1}s cooldown, then sending healthy data ...")
    time.sleep(cooldown + 1)
    deadline = time.time() + 60
    while time.time() < deadline and not seen["closed"]:
        for _ in range(50):
            producer.produce("checkout-events", json.dumps(make_event(False)).encode())
        producer.flush()
        poll_for(2)
    print("   breaker closed again:", seen["closed"])

    ok = all(seen.values())
    print("RESULT:", "PASS" if ok else "FAIL", seen)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()