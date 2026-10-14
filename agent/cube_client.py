"""Thin REST client for the Cube semantic layer."""
import json
import time

import httpx
import jwt

from config import CUBE_API_URL, CUBEJS_API_SECRET


class CubeError(RuntimeError):
    pass


class CubeClient:
    def __init__(self, base_url: str = CUBE_API_URL, secret: str = CUBEJS_API_SECRET, timeout: float = 60.0):
        self.base_url = base_url
        self.secret = secret
        self.http = httpx.Client(timeout=timeout)

    def _headers(self) -> dict:
        now = int(time.time())
        token = jwt.encode({"iat": now, "exp": now + 3600}, self.secret, algorithm="HS256")
        return {"Authorization": token}

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            r = self.http.get(f"{self.base_url}{path}", params=params, headers=self._headers())
        except httpx.HTTPError as e:
            raise CubeError(f"Cannot reach Cube at {self.base_url}: {e}") from e
        data = r.json()
        if r.status_code >= 400 or "error" in data:
            raise CubeError(str(data.get("error", r.text)))
        return data

    def meta(self) -> dict:
        return self._get("/v1/meta")

    def load(self, query: dict) -> dict:
        """Run a query. Cube answers 'Continue wait' while it builds the result - poll."""
        for _ in range(40):
            try:
                r = self.http.post(f"{self.base_url}/v1/load", json={"query": query}, headers=self._headers())
            except httpx.HTTPError as e:
                raise CubeError(f"Cannot reach Cube at {self.base_url}: {e}") from e
            data = r.json()
            if data.get("error") == "Continue wait":
                time.sleep(1)
                continue
            if r.status_code >= 400 or "error" in data:
                raise CubeError(str(data.get("error", r.text)))
            return data
        raise CubeError("Query timed out waiting for the warehouse.")

    def sql(self, query: dict) -> tuple[str, list]:
        """The exact SQL Cube generates for a query (for the UI's 'View SQL' button)."""
        data = self._get("/v1/sql", {"query": json.dumps(query)})
        sql, params = data["sql"]["sql"]
        return sql, params


def shape_result(resp: dict) -> tuple[list[dict], list[dict]]:
    """Turn a Cube /load response into UI-friendly columns + typed rows."""
    ann = resp.get("annotation", {})
    cols: list[dict] = []
    for key, a in ann.get("timeDimensions", {}).items():
        parts = key.split(".")
        if len(parts) == 3:  # only grouped time dimensions, e.g. orders.order_date.quarter
            cols.append({"key": key, "label": a.get("shortTitle") or a.get("title") or key, "kind": "time", "granularity": parts[2], "format": None})
    for key, a in ann.get("dimensions", {}).items():
        cols.append({"key": key, "label": a.get("shortTitle") or a.get("title") or key, "kind": "dimension", "format": None})
    for key, a in ann.get("measures", {}).items():
        cols.append({"key": key, "label": a.get("shortTitle") or a.get("title") or key, "kind": "measure", "format": a.get("format")})

    rows = []
    for raw in resp.get("data", []):
        row = {}
        for c in cols:
            v = raw.get(c["key"])
            row[c["key"]] = float(v) if (c["kind"] == "measure" and v is not None) else v
        rows.append(row)
    return cols, rows
