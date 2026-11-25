import argparse
from common import get_catalog

p = argparse.ArgumentParser()
p.add_argument("--table", default="ecommerce.checkout_raw")
p.add_argument("--snapshot-id", type=int, required=True)
p.add_argument("--yes", action="store_true", help="actually perform the rollback")
args = p.parse_args()

table = get_catalog().load_table(args.table)
before = table.current_snapshot().snapshot_id
print(f"Current snapshot: {before}")
print(f"Target snapshot:  {args.snapshot_id}")

if not args.yes:
    print("Dry run. Add --yes to roll back.")
else:
    manage = table.manage_snapshots()
    if hasattr(manage, "rollback_to_snapshot"):
        manage.rollback_to_snapshot(args.snapshot_id).commit()
    else:
        manage.set_current_snapshot(snapshot_id=args.snapshot_id).commit()
    table.refresh()
    print(f"Rolled back. Current snapshot is now {table.current_snapshot().snapshot_id}")
    print("Old files are kept, so you can roll forward again with the old snapshot id.")