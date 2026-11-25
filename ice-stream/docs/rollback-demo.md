# Rollback and re-fetch demo

1. Healthy data was loaded, then a burst with 30% NULL values arrived.
2. `time_travel.py --before <time>` shows the table before and after the anomaly.
3. `rollback.py --snapshot-id <id> --yes` restores the earlier state.
4. `replay_dlq.py` repairs quarantined records and re-sends them to `checkout-clean`.

## My run

```
(paste the output of time_travel.py here)
(paste the output of rollback.py here)
(paste the output of replay_dlq.py here)
```