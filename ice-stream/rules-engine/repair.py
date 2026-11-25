def repair(event: dict):
    """Try to fix common problems. Returns a fixed copy, or None if it cannot be saved."""
    e = dict(event)
    if "tax" in e and "tax_amount" not in e:
        e["tax_amount"] = e.pop("tax")          # undo column rename
    e.pop("coupon_code", None)                  # drop the extra column
    if isinstance(e.get("total"), str):         # undo type change
        try:
            e["total"] = float(e["total"])
        except ValueError:
            return None
    # tax is 8% of the subtotal, so total = subtotal * 1.08
    if e.get("tax_amount") is None and isinstance(e.get("total"), (int, float)):
        e["tax_amount"] = round(e["total"] / 1.08 * 0.08, 2)
    if e.get("total") is None and isinstance(e.get("tax_amount"), (int, float)):
        e["total"] = round(e["tax_amount"] / 0.08 * 1.08, 2)
    return e