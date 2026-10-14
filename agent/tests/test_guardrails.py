"""Unit tests for cost governance - no services required."""
import pytest

from catalog import Catalog
from guardrails import GuardrailError, SemanticQuery, compile_query

META = {"cubes": [{
    "name": "orders",
    "measures": [
        {"name": "orders.revenue", "shortTitle": "Revenue", "type": "number"},
        {"name": "orders.margin_pct", "shortTitle": "Gross Margin %", "type": "number"},
    ],
    "dimensions": [
        {"name": "orders.region", "shortTitle": "Region", "type": "string"},
        {"name": "orders.country", "shortTitle": "Country", "type": "string"},
        {"name": "orders.shipping_mode", "shortTitle": "Shipping Mode", "type": "string"},
        {"name": "orders.product_category", "shortTitle": "Category", "type": "string"},
        {"name": "orders.order_date", "shortTitle": "Order Date", "type": "time"},
    ],
}]}
CAT = Catalog(META)


def q(**kw):
    return SemanticQuery(**{"measures": ["orders.revenue"], **kw})


def test_valid_query_compiles_with_time_series():
    cube, _ = compile_query(q(dimensions=["orders.region"], granularity="quarter", date_range="last quarter"), CAT)
    assert cube["measures"] == ["orders.revenue"]
    assert cube["timeDimensions"][0] == {"dimension": "orders.order_date", "dateRange": "last quarter", "granularity": "quarter"}


def test_unknown_measure_is_rejected():
    with pytest.raises(GuardrailError, match="Unknown measure"):
        compile_query(q(measures=["orders.profit"]), CAT)


def test_sql_injection_style_member_is_rejected():
    with pytest.raises(GuardrailError):
        compile_query(q(dimensions=["orders.region; DROP TABLE orders"]), CAT)


def test_dimension_cannot_be_used_as_measure():
    with pytest.raises(GuardrailError, match="not a measure|Unknown measure"):
        compile_query(q(measures=["orders.region"]), CAT)


def test_default_date_range_and_limit_are_applied():
    cube, notes = compile_query(q(), CAT)
    assert cube["timeDimensions"][0]["dateRange"] == "last 12 months"
    assert cube["limit"] == 200
    assert any("default" in n.lower() for n in notes)


def test_limit_is_capped():
    cube, notes = compile_query(q(limit=10_000_000), CAT)
    assert cube["limit"] == 500
    assert any("capped" in n.lower() for n in notes)


def test_too_many_dimensions_rejected():
    dims = ["orders.region", "orders.country", "orders.shipping_mode", "orders.product_category"]
    with pytest.raises(GuardrailError, match="At most 3"):
        compile_query(q(dimensions=dims), CAT)


def test_bad_date_ranges_rejected():
    for bad in ["whenever", ["2026-13-01", "2026-14-01"], ["2026-09-30", "2026-07-01"], ["2000-01-01", "2026-01-01"], ["2026-01-01"]]:
        with pytest.raises(GuardrailError):
            compile_query(q(date_range=bad), CAT)


def test_explicit_date_range_passes():
    cube, _ = compile_query(q(date_range=["2026-07-01", "2026-09-30"]), CAT)
    assert cube["timeDimensions"][0]["dateRange"] == ["2026-07-01", "2026-09-30"]


def test_filter_on_measure_rejected_and_values_required():
    with pytest.raises(GuardrailError):
        compile_query(q(filters=[{"member": "orders.revenue", "operator": "gt", "values": ["1"]}]), CAT)
    with pytest.raises(GuardrailError, match="needs values"):
        compile_query(q(filters=[{"member": "orders.region", "operator": "equals"}]), CAT)


def test_valid_filter_compiles():
    cube, _ = compile_query(q(filters=[{"member": "orders.region", "operator": "equals", "values": ["Europe"]}]), CAT)
    assert cube["filters"] == [{"member": "orders.region", "operator": "equals", "values": ["Europe"]}]


def test_order_outside_query_is_dropped_with_note():
    cube, notes = compile_query(q(order={"orders.margin_pct": "desc"}), CAT)
    assert "order" not in cube
    assert any("Ignored ordering" in n for n in notes)
