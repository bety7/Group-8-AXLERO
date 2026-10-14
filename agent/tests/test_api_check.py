"""API check: does the LLM translate natural language into the right semantic query?

Needs Cube + an LLM. Run with:  RUN_LLM_TESTS=1 pytest tests/test_api_check.py
"""
import asyncio
import os

import pytest

from agent import run_agent

pytestmark = pytest.mark.skipif(os.getenv("RUN_LLM_TESTS") != "1", reason="set RUN_LLM_TESTS=1 to run LLM tests")


async def _collect(question: str) -> list[dict]:
    return [e async for e in run_agent([{"role": "user", "content": question}])]


def test_show_me_european_sales():
    events = asyncio.run(_collect("Show me European sales by quarter"))
    queries = [e["query"] for e in events if e["type"] == "tool_result" and e["ok"]]
    assert queries, "Agent did not run a successful semantic query"
    q = queries[0]
    assert "orders.revenue" in q["measures"]
    assert any(f["member"] == "orders.region" and f["values"] == ["Europe"] for f in q.get("filters", []))


def test_agent_refuses_unknown_metric():
    events = asyncio.run(_collect("What is our customer churn rate?"))
    assert not any(e["type"] == "tool_result" and e["ok"] and "churn" in str(e["query"]) for e in events)
