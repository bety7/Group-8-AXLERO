import argparse
import json
import time
from collections import Counter
from datetime import datetime, timezone
from confluent_kafka import Consumer, Producer
from breaker import CircuitBreaker, State
from rules import load_rules, validate_event


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default="localhost:9092")
    p.add_argument("--source", default="checkout-events")
    p.add_argument("--clean", default="checkout-clean")
    p.add_argument("--dlq", default="checkout-dlq")
    args = p.parse_args()

    rules = load_rules()
    producer = Producer({"bootstrap.servers": args.bootstrap, "linger.ms": 20})

    def on_change(old, new, rate):
        event = {
            "type": "breaker",
            "from": old.value,
            "to": new.value,
            "error_rate": round(rate, 4),
            "at": now_iso(),
            "reason": f"error rate {rate:.1%} vs threshold {rules['breaker']['error_rate_threshold']:.1%}",
        }
        print(f"[{event['at']}] BREAKER {old.value} -> {new.value} (error rate {rate:.2%})", flush=True)
        producer.produce("breaker-events", json.dumps(event).encode("utf-8"))
        producer.flush()

    breaker = CircuitBreaker.from_config(rules["breaker"], on_change=on_change)
    consumer = Consumer({
        "bootstrap.servers": args.bootstrap,
        "group.id": "ice-guard",
        "auto.offset.reset": "latest",
    })
    consumer.subscribe([args.source])

    counts = Counter()
    last_report = time.time()
    print(f"Guard running: {args.source} -> {args.clean} / {args.dlq}", flush=True)
    try:
        while True:
            msg = consumer.poll(0.5)
            if msg is not None and not msg.error():
                raw = msg.value().decode("utf-8", errors="replace")
                try:
                    errors = validate_event(json.loads(raw), rules)
                except json.JSONDecodeError:
                    errors = ["invalid_json"]

                breaker.record(bool(errors))

                if breaker.state == State.CLOSED and not errors:
                    producer.produce(args.clean, raw.encode("utf-8"))
                    counts["clean"] += 1
                else:
                    reason = ",".join(errors) if errors else f"circuit_{breaker.state.value.lower()}"
                    dlq_record = {
                        "error_reason": reason,
                        "breaker_state": breaker.state.value,
                        "quarantined_at": now_iso(),
                        "raw_payload": raw,
                    }
                    producer.produce(args.dlq, json.dumps(dlq_record).encode("utf-8"))
                    counts["dlq"] += 1
                producer.poll(0)

            if time.time() - last_report >= 5:
                print(f"-- 5s: {counts['clean']} clean, {counts['dlq']} to DLQ, breaker={breaker.state.value}", flush=True)
                counts.clear()
                last_report = time.time()
    except KeyboardInterrupt:
        print("Stopping guard...")
    finally:
        consumer.close()
        producer.flush()


if __name__ == "__main__":
    main()