import argparse
from datetime import datetime, timezone
from common import get_catalog

p = argparse.ArgumentParser()
p.add_argument("--table", default="ecommerce.checkout_raw")
p.add_argument("--before", required=True, help="UTC time, e.g. 2026-11-24T10:30:00")
args = p.parse_args()

table = get_catalog().load_table(args.table)
cutoff = datetime.fromisoformat(args.before).replace(tzinfo=timezone.utc)
old = table.snapshot_as_of_timestamp(int(cutoff.timestamp() * 1000))
now = table.current_snapshot()


def show(label, snapshot_id):
    arrow = table.scan(snapshot_id=snapshot_id).to_arrow()
    nulls = arrow.column("tax_amount").null_count
    print(f"{label:<8} snapshot={snapshot_id}  rows={arrow.num_rows}  null tax_amount={nulls}")


if old is None:
    print("No snapshot existed before that time.")
else:
    show("BEFORE", old.snapshot_id)
show("NOW", now.snapshot_id)