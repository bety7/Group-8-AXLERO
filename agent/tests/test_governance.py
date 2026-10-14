"""Governance audit (needs `docker compose up -d` + dbt seed/run).

Proves that a governed question ("last quarter's revenue") returns the exact same
number on every call, and that it matches an independent SQL query on the warehouse.
"""
import os
from datetime import date
from decimal import Decimal

import psycopg
import pytest

from cube_client import CubeClient, CubeError
from dates import quarter_bounds


@pytest.fixture(scope="module")
def client():
    c = CubeClient()
    try:
        c.meta()
    except CubeError:
        pytest.skip("Cube is not running (docker compose up -d)")
    return c


def _cube_revenue(client, start, end):
    q = {"measures": ["orders.revenue"], "timeDimensions": [{"dimension": "orders.order_date", "dateRange": [start.isoformat(), end.isoformat()]}]}
    return Decimal(client.load(q)["data"][0]["orders.revenue"])


@pytest.mark.parametrize("offset", [-1, -2])
def test_quarter_revenue_is_identical_every_time(client, offset):
    start, end = quarter_bounds(date.today(), offset)
    values = {_cube_revenue(client, start, end) for _ in range(10)}
    assert len(values) == 1, f"Non-deterministic revenue: {values}"


@pytest.mark.parametrize("offset", [-1, -2])
def test_cube_matches_warehouse_ground_truth(client, offset):
    start, end = quarter_bounds(date.today(), offset)
    dsn = (
        f"host={os.getenv('PGHOST', 'localhost')} port={os.getenv('PGPORT', '5432')} dbname={os.getenv('PGDATABASE', 'metricmind')} "
        f"user={os.getenv('PGUSER', 'metricmind')} password={os.getenv('PGPASSWORD', 'metricmind')}"
    )
    with psycopg.connect(dsn) as conn:
        truth = conn.execute("select sum(revenue) from analytics.fct_orders where order_date between %s and %s", (start, end)).fetchone()[0]
    assert _cube_revenue(client, start, end) == truth
