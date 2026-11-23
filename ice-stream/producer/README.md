# Producer

Generates mock e-commerce checkout events and sends them to Kafka.

## Usage

    python main.py --eps 1000 --null-rate 0.05 --drift-rate 0.01

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| --bootstrap | localhost:9092 | Kafka bootstrap server |
| --topic | checkout-events | Target topic |
| --eps | 1000 | Events per second |
| --null-rate | 0.0 | Fraction of events with one NULL field |
| --drift-rate | 0.0 | Fraction of events with schema drift |