from pathlib import Path
import yaml

PY_TYPES = {"str": (str,), "int": (int,), "float": (int, float)}


def load_rules(path=None):
    path = Path(path) if path else Path(__file__).with_name("rules.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_event(event, rules) -> list:
    """Return a list of error strings. An empty list means the event is valid."""
    if not isinstance(event, dict):
        return ["not_an_object"]
    errors = []
    types = rules["types"]
    for field in rules["required_fields"]:
        if field not in event:
            errors.append(f"missing_field:{field}")
        elif event[field] is None:
            errors.append(f"null_value:{field}")
        else:
            value = event[field]
            if isinstance(value, bool) or not isinstance(value, PY_TYPES[types[field]]):
                errors.append(f"wrong_type:{field}")
    for field in event:
        if field not in types:
            errors.append(f"unexpected_field:{field}")
    return errors