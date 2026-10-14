"""The agentic orchestrator: LLM + one governed tool, with a streaming event protocol."""
import asyncio
import json
import time
from datetime import date
from typing import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import ValidationError

from catalog import Catalog
from config import (
    ANTHROPIC_MODEL,
    LLM_PROVIDER,
    MAX_QUERIES_PER_QUESTION,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from cube_client import CubeClient, CubeError, shape_result
from dates import calendar_hints
from guardrails import GuardrailError, QuerySemanticLayer, SemanticQuery, compile_query

SYSTEM_PROMPT = """You are MetricMind, a governed analytics agent for an enterprise.

HARD RULES
1. You never write SQL. The ONLY way to get data is the QuerySemanticLayer tool, which compiles governed metric definitions.
2. Use ONLY measures and dimensions from the catalog below. If a request needs something that is not there, say so and offer the closest governed metric.
3. Never invent numbers. Every figure you state must come from a tool result in this conversation.
4. Never redefine metrics. "Margin" means orders.margin_pct. "Quarter" means calendar quarter.
5. Always pass an explicit date_range. Use the exact ranges from the calendar below instead of doing date maths.
6. Keep queries narrow (max 3 dimensions) and budget your calls: at most {budget} queries per question.
7. Use filter values exactly as listed in the catalog (e.g. "Europe").

ROOT-CAUSE QUESTIONS ("why did X change?") - work in steps, stopping when you have the answer:
  Step 1 Confirm: query the headline metric as a quarterly time series (granularity "quarter") for the filtered scope, covering both periods.
  Step 2 Decompose: query the component measures (revenue, material_cost, shipping_cost) for the same scope and periods. Work out which component moved most relative to revenue.
  Step 3 Drill down: break the biggest mover down by the most relevant dimension (e.g. shipping_mode, product_category, country, customer_segment).
  Step 4 Benchmark if useful: compare with the other regions to show whether the change is local.
  Then answer: lead with the conclusion, support it with 2-4 numbers, and give one suggested next action.

STYLE
Short, executive-friendly markdown. Lead with the answer. Bold the key numbers. Currency like $1.2M, percentages to 1 decimal, changes in margin in percentage points ("pp"). Charts and tables for every query are shown to the user automatically, so do not repeat tables.

CALENDAR
{calendar}

CATALOG
{catalog}
"""


def build_llm():
    if LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=ANTHROPIC_MODEL, temperature=0, max_tokens=2048)
    from langchain_ollama import ChatOllama

    return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)


# ---- cached catalog + dimension values (refreshed every 5 minutes) ----
_ctx: dict = {"ts": 0.0, "catalog": None, "values": {}}


def get_context(client: CubeClient) -> tuple[Catalog, dict[str, list[str]]]:
    if _ctx["catalog"] is None or time.time() - _ctx["ts"] > 300:
        catalog = Catalog(client.meta())
        values: dict[str, list[str]] = {}
        for dim in catalog.categorical_dimensions():
            resp = client.load({"dimensions": [dim], "order": {dim: "asc"}, "limit": 30})
            values[dim] = [r[dim] for r in resp.get("data", []) if r.get(dim) is not None]
        _ctx.update(ts=time.time(), catalog=catalog, values=values)
    return _ctx["catalog"], _ctx["values"]


def build_system_prompt(catalog: Catalog, values: dict[str, list[str]], today: date | None = None) -> str:
    return SYSTEM_PROMPT.format(
        budget=MAX_QUERIES_PER_QUESTION, calendar=calendar_hints(today), catalog=catalog.prompt_block(values)
    )


def _text(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def _to_langchain(history: list[dict]) -> list:
    return [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]


async def _run_tool(client: CubeClient, catalog: Catalog, call: dict) -> tuple[ToolMessage, dict]:
    started = time.perf_counter()
    try:
        query = SemanticQuery.model_validate(call["args"])
        cube_query, notes = compile_query(query, catalog)
        resp = await asyncio.to_thread(client.load, cube_query)
        try:
            sql, params = await asyncio.to_thread(client.sql, cube_query)
        except CubeError:
            sql, params = None, []
        cols, rows = shape_result(resp)
        event = {
            "type": "tool_result", "id": call["id"], "ok": True, "query": cube_query, "sql": sql, "params": params,
            "columns": cols, "rows": rows, "notes": notes, "row_count": len(rows),
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        }
        for_llm = {
            "columns": [{"key": c["key"], "label": c["label"], "format": c["format"]} for c in cols],
            "rows": rows[:60], "row_count": len(rows), "truncated": len(rows) > 60, "notes": notes,
        }
        return ToolMessage(content=json.dumps(for_llm, default=str), tool_call_id=call["id"]), event
    except (GuardrailError, CubeError, ValidationError) as e:
        msg = str(e)
        event = {"type": "tool_result", "id": call["id"], "ok": False, "error": msg}
        return ToolMessage(content=f"ERROR: {msg}\nFix the query and try again.", tool_call_id=call["id"]), event


async def run_agent(history: list[dict]) -> AsyncIterator[dict]:
    client = CubeClient()
    try:
        catalog, values = await asyncio.to_thread(get_context, client)
    except CubeError as e:
        yield {"type": "error", "message": f"The semantic layer is unreachable. Start it with `docker compose up -d`. ({e})"}
        return

    llm = build_llm().bind_tools([QuerySemanticLayer])
    messages = [SystemMessage(build_system_prompt(catalog, values)), *_to_langchain(history)]
    queries_used = 0

    try:
        for _ in range(MAX_QUERIES_PER_QUESTION + 2):
            full = None
            async for chunk in llm.astream(messages):
                text = _text(chunk.content)
                if text:
                    yield {"type": "token", "text": text}
                full = chunk if full is None else full + chunk
            if full is None:
                break
            messages.append(full)
            if not full.tool_calls:
                break

            for call in full.tool_calls:
                yield {"type": "tool_start", "id": call["id"], "args": call["args"]}
                if queries_used >= MAX_QUERIES_PER_QUESTION:
                    msg = f"Query budget of {MAX_QUERIES_PER_QUESTION} reached. Answer with what you have."
                    messages.append(ToolMessage(content=f"ERROR: {msg}", tool_call_id=call["id"]))
                    yield {"type": "tool_result", "id": call["id"], "ok": False, "error": msg}
                    continue
                queries_used += 1
                tool_msg, event = await _run_tool(client, catalog, call)
                messages.append(tool_msg)
                yield event
    except Exception as e:  # LLM provider down, bad key, etc.
        hint = "Is Ollama running (`ollama serve`) and the model pulled?" if LLM_PROVIDER == "ollama" else "Check ANTHROPIC_API_KEY."
        yield {"type": "error", "message": f"LLM error ({LLM_PROVIDER}): {e}. {hint}"}
        return

    yield {"type": "done"}
