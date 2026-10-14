"""The governed metric catalog, built from Cube's /meta endpoint."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    name: str
    kind: str  # "measure" | "dimension"
    title: str
    type: str
    description: str
    format: str | None = None


class Catalog:
    def __init__(self, meta: dict):
        self.members: dict[str, Member] = {}
        for cube in meta.get("cubes", []):
            for kind, key in (("measure", "measures"), ("dimension", "dimensions")):
                for m in cube.get(key, []):
                    self.members[m["name"]] = Member(
                        name=m["name"],
                        kind=kind,
                        title=m.get("shortTitle") or m.get("title") or m["name"],
                        type=m.get("type", ""),
                        description=m.get("description") or "",
                        format=m.get("format"),
                    )

    def require(self, name: str, kind: str, *, time: bool = False) -> Member:
        m = self.members.get(name)
        if m is None:
            close = ", ".join(sorted(n for n, x in self.members.items() if x.kind == kind))
            raise ValueError(f"Unknown {kind} '{name}'. Available {kind}s: {close}")
        if m.kind != kind:
            raise ValueError(f"'{name}' is a {m.kind}, not a {kind}.")
        if time and m.type != "time":
            raise ValueError(f"'{name}' is not a time dimension.")
        return m

    @property
    def default_time_dimension(self) -> str | None:
        return next((n for n, m in self.members.items() if m.kind == "dimension" and m.type == "time"), None)

    def names(self, kind: str) -> list[str]:
        return [n for n, m in self.members.items() if m.kind == kind]

    def categorical_dimensions(self) -> list[str]:
        return [n for n, m in self.members.items() if m.kind == "dimension" and m.type == "string"]

    def prompt_block(self, values: dict[str, list[str]] | None = None) -> str:
        values = values or {}
        out = ["MEASURES (governed formulas - never redefine them):"]
        for m in (x for x in self.members.values() if x.kind == "measure"):
            out.append(f"- {m.name}: {m.title}. {m.description}")
        out.append("\nDIMENSIONS:")
        for m in (x for x in self.members.values() if x.kind == "dimension"):
            vals = values.get(m.name)
            suffix = f" Values: {' | '.join(vals)}" if vals else ""
            out.append(f"- {m.name} ({m.type}): {m.description}{suffix}")
        return "\n".join(out)

    def public(self) -> list[dict]:
        return [
            {"name": m.name, "title": m.title, "kind": m.kind, "type": m.type, "description": m.description, "format": m.format}
            for m in self.members.values()
        ]
