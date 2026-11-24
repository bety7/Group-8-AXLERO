import argparse
from datetime import datetime, timezone
from common import get_catalog

p = argparse.ArgumentParser()
p.add_argument("--table", default="ecommerce.checkout_raw")
args = p.parse_args()

table = get_catalog().load_table(args.table)
snaps = table.snapshots()
print(f"{len(snaps)} snapshots in {args.table}")
print(f"{'snapshot_id':<22}{'committed (UTC)':<22}{'operation':<12}added_records")
for s in snaps:
    ts = datetime.fromtimestamp(s.timestamp_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    summary = s.summary
    op = summary.operation.value if summary else "?"
    extra = getattr(summary, "additional_properties", {}) or {}
    print(f"{s.snapshot_id:<22}{ts:<22}{op:<12}{extra.get('added-records', '?')}")