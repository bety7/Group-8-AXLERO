import argparse, json, random, time, uuid
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

def make_event(i, bad_rate):
    event = {
        "event_id": str(uuid.uuid4()),
        "order_id": f"ORD-{100000+i}",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "amount": round(random.uniform(5, 850), 2),
        "currency": "INR",
        "customer_id": f"CUST-{random.randint(1000,9999)}"
    }
    if random.random() < bad_rate:
        fault = random.choice(["null", "negative", "schema"])
        if fault == "null":
            event["amount"] = None
        elif fault == "negative":
            event["amount"] = -round(random.uniform(1, 100), 2)
        else:
            event.pop("customer_id", None)
            event["unexpected_field"] = "schema-v2"
    return event

def main():
    parser = argparse.ArgumentParser(description="Generate mock e-commerce checkout events")
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--bad-rate", type=float, default=0.04)
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--topic", default="checkout-events")
    parser.add_argument("--delay", type=float, default=0.03)
    args = parser.parse_args()
    try:
        producer = KafkaProducer(
            bootstrap_servers=args.bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=5
        )
    except NoBrokersAvailable:
        raise SystemExit("Kafka broker not reachable. Start the stack with: docker compose up --build")
    for i in range(args.count):
        event = make_event(i, args.bad_rate)
        producer.send(args.topic, event)
        if i % 25 == 0:
            print(f"Sent {i+1}/{args.count} events")
        time.sleep(args.delay)
    producer.flush()
    producer.close()
    print(f"Done. Sent {args.count} events to {args.topic}.")

if __name__ == "__main__":
    main()
