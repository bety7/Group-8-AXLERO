"""Calendar helpers so the LLM never has to do date arithmetic."""
from datetime import date, timedelta


def _add_months(d: date, n: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    return date(y, m + 1, 1)


def quarter_start(d: date) -> date:
    return date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def quarter_bounds(today: date, offset: int) -> tuple[date, date]:
    """offset=-1 -> last complete quarter, -2 -> the one before, 0 -> current quarter."""
    start = _add_months(quarter_start(today), 3 * offset)
    return start, _add_months(start, 3) - timedelta(days=1)


def label(start: date) -> str:
    return f"{start.year} Q{(start.month - 1) // 3 + 1}"


def calendar_hints(today: date | None = None) -> str:
    today = today or date.today()
    lines = [f"Today is {today.isoformat()}."]
    for offset, name in [(-1, "last quarter"), (-2, "the quarter before last"), (-5, "the same quarter one year before last quarter")]:
        s, e = quarter_bounds(today, offset)
        lines.append(f'- {name} = {label(s)} = ["{s.isoformat()}", "{e.isoformat()}"]')
    s, _ = quarter_bounds(today, -4)
    _, e = quarter_bounds(today, -1)
    lines.append(f'- last 4 complete quarters = ["{s.isoformat()}", "{e.isoformat()}"]')
    return "\n".join(lines)
