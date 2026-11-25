import argparse
import json
from pathlib import Path
from confluent_kafka import Producer
from iceberg_tools.common import get_catalog
from repair import repair
from rules import load_rules, validate_event

SEEN_FILE = Path(__file__).with_name(".replayed_ids.txt")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--clean-topic", default="checkout-clean")
    args = p.parse_args()

    rules = load_rules()
    seen = set(SEEN_FILE.read_text().split()) if SEEN_FILE.exists() else set()
    rows = get_catalog().load_table("ecommerce.checkout_dlq").scan().to_arrow().to_pylist()
    producer = Producer({"bootstrap.servers": "localhost:9092"})

    replayed = skipped = unrecoverable = 0
    for row in rows:
        try:
            event = json.loads(row["raw_payload"])
        except (TypeError, json.JSONDecodeError):
            unrecoverable += 1
            continue
        fixed = repair(event) if isinstance(event, dict) else None
        if fixed is None or validate_event(fixed, rules):
            unrecoverable += 1
            continue
        if fixed["order_id"] in seen:
            skipped += 1
            continue
        if not args.dry_run:
            producer.produce(args.clean_topic, json.dumps(fixed).encode("utf-8"))
            seen.add(fixed["order_id"])
        replayed += 1

    producer.flush()
    if not args.dry_run:
        SEEN_FILE.write_text("\n".join(sorted(seen)))
    mode = "DRY RUN: would replay" if args.dry_run else "Replayed"
    print(f"{mode} {replayed}; already replayed {skipped}; unrecoverable {unrecoverable}; DLQ rows {len(rows)}")


if __name__ == "__main__":
    main()