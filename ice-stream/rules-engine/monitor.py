import argparse
import json
import time
from collections import Counter
from confluent_kafka import Consumer
from rules import load_rules, validate_event


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default="localhost:9092")
    p.add_argument("--topic", default="checkout-events")
    args = p.parse_args()

    rules = load_rules()
    consumer = Consumer({
        "bootstrap.servers": args.bootstrap,
        "group.id": "ice-monitor",
        "auto.offset.reset": "latest",
    })
    consumer.subscribe([args.topic])
    total = bad = 0
    reasons = Counter()
    last = time.time()
    print(f"Monitoring '{args.topic}' ... (Ctrl+C to stop)")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is not None and not msg.error():
                total += 1
                try:
                    errors = validate_event(json.loads(msg.value()), rules)
                except json.JSONDecodeError:
                    errors = ["invalid_json"]
                if errors:
                    bad += 1
                    reasons.update(errors)
                    print(f"FLAG  {', '.join(errors)}", flush=True)
            if time.time() - last >= 5:
                rate = (bad / total) if total else 0
                print(f"-- last 5s: {total} events, {bad} bad ({rate:.1%}) {dict(reasons)}", flush=True)
                total = bad = 0
                reasons.clear()
                last = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()