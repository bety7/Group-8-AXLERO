import argparse
from common import get_catalog

p = argparse.ArgumentParser()
p.add_argument("--table", default="ecommerce.checkout_raw")
args = p.parse_args()

table = get_catalog().load_table(args.table)
print("Table:", args.table)
print("Schema:")
print(table.schema())
print("Partition spec:", table.spec())
current = table.current_snapshot()
print("Current snapshot:", current.snapshot_id if current else None)
print("Snapshots:", len(table.snapshots()))
print("Rows:", table.scan().to_arrow().num_rows)