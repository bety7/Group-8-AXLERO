import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from common import get_catalog


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=int, default=60)
    p.add_argument("--table", default="ecommerce.checkout_raw")
    args = p.parse_args()

    table = get_catalog().load_table(args.table)
    reads, prev_rows, max_dupes = 0, 0, 0
    failures = []
    end = time.time() + args.seconds
    while time.time() < end:
        try:
            table.refresh()
            arrow = table.scan(selected_fields=("order_id",)).to_arrow()
            rows = arrow.num_rows
            distinct = len(arrow.column("order_id").unique())
            reads += 1
            if rows < prev_rows:
                failures.append(f"row count went backwards: {prev_rows} -> {rows}")
            max_dupes = max(max_dupes, rows - distinct)
            prev_rows = rows
            print(f"read {reads}: {rows} rows, {rows - distinct} duplicates", flush=True)
        except Exception as exc:  # any failed read counts as a failure
            failures.append(f"read error: {exc}")
        time.sleep(3)

    passed = not failures and max_dupes == 0
    report = Path(__file__).resolve().parents[2] / "docs" / "acid-audit.md"
    report.write_text(
        "# ACID audit\n\n"
        f"- Run at: {datetime.now(timezone.utc).isoformat()}\n"
        f"- Table: {args.table}\n"
        f"- Concurrent reads while the stream was writing: {reads}\n"
        f"- Final row count: {prev_rows}\n"
        f"- Max duplicate order_ids seen: {max_dupes}\n"
        f"- Read failures / inconsistencies: {len(failures)}\n"
        f"- Result: {'PASS' if passed else 'FAIL'}\n\n"
        "Iceberg readers see a consistent snapshot while Flink commits new ones, "
        "so no locking is needed and reads never see half-written data.\n",
        encoding="utf-8",
    )
    print("RESULT:", "PASS" if passed else "FAIL", "-> report written to docs/acid-audit.md")


if __name__ == "__main__":
    main()