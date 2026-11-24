import argparse
import json
import time
from confluent_kafka import Producer
from schema import generate_transaction
from injectors import inject_nulls, inject_drift


def parse_args():
    p = argparse.ArgumentParser(description="Ice Stream mock transaction producer")
    p.add_argument("--bootstrap", default="localhost:9092")
    p.add_argument("--topic", default="checkout-events")
    p.add_argument("--eps", type=int, default=1000, help="events per second")
    p.add_argument("--null-rate", type=float, default=0.0, help="fraction of events with a NULL field")
    p.add_argument("--drift-rate", type=float, default=0.0, help="fraction of events with schema drift")
    return p.parse_args()


def main():
    args = parse_args()
    producer = Producer({
        "bootstrap.servers": args.bootstrap,
        "linger.ms": 20,
        "batch.num.messages": 10000,
        "compression.type": "lz4",
    })
    print(f"Producing {args.eps} events/sec to '{args.topic}' "
          f"(null rate {args.null_rate}, drift rate {args.drift_rate})")

    try:
        while True:
            start = time.time()
            for _ in range(args.eps):
                event = generate_transaction()
                event = inject_nulls(event, args.null_rate)
                event = inject_drift(event, args.drift_rate)
                try:
                    producer.produce(args.topic, json.dumps(event).encode("utf-8"))
                except BufferError:
                    producer.poll(0.5)
                producer.poll(0)
            elapsed = time.time() - start
            if elapsed < 1:
                time.sleep(1 - elapsed)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        producer.flush()


if __name__ == "__main__":
    main()