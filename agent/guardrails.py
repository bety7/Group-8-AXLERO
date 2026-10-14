"""Cost + correctness governance.

The LLM never touches SQL. It proposes a *semantic query* (this schema), and this
module validates and compiles it into a bounded Cube query. Anything that is not a
governed member, is unbounded, or is too wide is rejected with an actionable message
the model can use to self-correct.
"""
import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from catalog import Catalog
from config import (
    DEFAULT_DATE_RANGE,
    DEFAULT_ROW_LIMIT,
    MAX_DIMENSIONS,
    MAX_FILTER_VALUES,
    MAX_MEASURES,
    MAX_RANGE_DAYS,
    MAX_ROWS,
)


class GuardrailError(ValueError):
    """The query violates a governance rule."""


class Filter(BaseModel):
    member: str = Field(description="A dimension name, e.g. orders.region")
    operator: Literal["equals", "notEquals", "contains", "notContains", "gt", "gte", "lt", "lte", "set", "notSet"]
    values: list[str] = Field(default_factory=list, description="Filter values as strings. Empty for set/notSet.")


class SemanticQuery(BaseModel):
    measures: list[str] = Field(description="Governed measures, e.g. ['orders.revenue']. At least one.")
    dimensions: list[str] = Field(default_factory=list, description="Dimensions to group by, e.g. ['orders.region']. Max 3.")
    time_dimension: str | None = Field(default=None, description="Time dimension to filter/group on. Defaults to orders.order_date.")
    granularity: Literal["day", "week", "month", "quarter", "year"] | None = Field(
        default=None, description="Group the time dimension into buckets (a time series). Omit for a single total."
    )
    date_range: str | list[str] | None = Field(
        default=None,
        description='Relative range like "last quarter", or two ISO dates ["2026-07-01","2026-09-30"]. Always provide one.',
    )
    filters: list[Filter] = Field(default_factory=list)
    order: dict[str, Literal["asc", "desc"]] = Field(default_factory=dict, description='e.g. {"orders.revenue": "desc"}')
    limit: int | None = Field(default=None, description=f"Max rows (hard cap {MAX_ROWS}).")


class QuerySemanticLayer(SemanticQuery):
    """Run a governed query against the enterprise semantic layer and return rows.
    This is the ONLY way to get data. Use only members from the catalog."""


_RELATIVE = re.compile(r"^(today|yesterday|(this|last) (week|month|quarter|year)|last \d{1,3} (days|weeks|months|quarters|years))$", re.I)


def _validate_range(r: str | list[str]) -> str | list[str]:
    if isinstance(r, str):
        if _RELATIVE.match(r.strip()):
            return r.strip().lower()
        raise GuardrailError(f'Unsupported date_range "{r}". Use e.g. "last quarter", "last 6 months", or two ISO dates.')
    if len(r) != 2:
        raise GuardrailError("date_range must be exactly two ISO dates: [start, end].")
    try:
        start, end = (date.fromisoformat(x) for x in r)
    except ValueError as e:
        raise GuardrailError(f"Invalid date in date_range: {e}") from e
    if start > end:
        raise GuardrailError("date_range start is after end.")
    if (end - start).days > MAX_RANGE_DAYS:
        raise GuardrailError(f"date_range spans more than {MAX_RANGE_DAYS} days. Narrow it.")
    return [start.isoformat(), end.isoformat()]


def compile_query(q: SemanticQuery, catalog: Catalog) -> tuple[dict, list[str]]:
    """Validate a SemanticQuery and compile it to a bounded Cube REST query. Returns (query, notes)."""
    notes: list[str] = []

    if not q.measures:
        raise GuardrailError("Provide at least one measure.")
    if len(q.measures) > MAX_MEASURES:
        raise GuardrailError(f"At most {MAX_MEASURES} measures per query.")
    if len(q.dimensions) > MAX_DIMENSIONS:
        raise GuardrailError(f"At most {MAX_DIMENSIONS} dimensions per query.")
    if len(set(q.measures)) != len(q.measures) or len(set(q.dimensions)) != len(q.dimensions):
        raise GuardrailError("Duplicate members in query.")

    try:
        for m in q.measures:
            catalog.require(m, "measure")
        for d in q.dimensions:
            catalog.require(d, "dimension")
        time_dim = q.time_dimension or catalog.default_time_dimension
        if time_dim is None:
            raise GuardrailError("The catalog has no time dimension.")
        catalog.require(time_dim, "dimension", time=True)
        if time_dim in q.dimensions:
            raise GuardrailError("Use time_dimension + granularity for time, not dimensions.")
    except ValueError as e:
        if isinstance(e, GuardrailError):
            raise
        raise GuardrailError(str(e)) from e

    if q.date_range is None:
        date_range: str | list[str] = DEFAULT_DATE_RANGE
        notes.append(f'No date range given - applied the default "{DEFAULT_DATE_RANGE}".')
    else:
        date_range = _validate_range(q.date_range)

    td: dict = {"dimension": time_dim, "dateRange": date_range}
    if q.granularity:
        td["granularity"] = q.granularity

    filters = []
    for f in q.filters:
        try:
            catalog.require(f.member, "dimension")
        except ValueError as e:
            raise GuardrailError(str(e)) from e
        if f.operator not in ("set", "notSet") and not f.values:
            raise GuardrailError(f"Filter on {f.member} needs values.")
        if len(f.values) > MAX_FILTER_VALUES:
            raise GuardrailError(f"Filter on {f.member} has more than {MAX_FILTER_VALUES} values.")
        item = {"member": f.member, "operator": f.operator}
        if f.operator not in ("set", "notSet"):
            item["values"] = f.values
        filters.append(item)

    limit = q.limit or DEFAULT_ROW_LIMIT
    if limit > MAX_ROWS:
        limit = MAX_ROWS
        notes.append(f"Row limit capped at {MAX_ROWS}.")
    elif q.limit is None:
        notes.append(f"Applied default row limit of {DEFAULT_ROW_LIMIT}.")

    allowed_order = set(q.measures) | set(q.dimensions) | {time_dim}
    order = {}
    for member, direction in q.order.items():
        if member in allowed_order:
            order[member] = direction
        else:
            notes.append(f"Ignored ordering by {member} (not part of the query).")

    cube_query: dict = {"measures": q.measures, "timeDimensions": [td], "limit": limit, "timezone": "UTC"}
    if q.dimensions:
        cube_query["dimensions"] = q.dimensions
    if filters:
        cube_query["filters"] = filters
    if order:
        cube_query["order"] = order
    return cube_query, notes
