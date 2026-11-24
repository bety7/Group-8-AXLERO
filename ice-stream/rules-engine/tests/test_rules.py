from rules import load_rules, validate_event

RULES = load_rules()


def good():
    return {"order_id": "a", "user_id": 1, "tax_amount": 1.5, "total": 20.0,
            "ts": "2026-11-17T10:00:00+00:00"}


def test_valid_event_has_no_errors():
    assert validate_event(good(), RULES) == []


def test_null_value_is_flagged():
    e = good(); e["tax_amount"] = None
    assert "null_value:tax_amount" in validate_event(e, RULES)


def test_renamed_column_is_flagged():
    e = good(); e["tax"] = e.pop("tax_amount")
    errors = validate_event(e, RULES)
    assert "missing_field:tax_amount" in errors
    assert "unexpected_field:tax" in errors


def test_extra_column_is_flagged():
    e = good(); e["coupon_code"] = "SAVE10"
    assert "unexpected_field:coupon_code" in validate_event(e, RULES)


def test_wrong_type_is_flagged():
    e = good(); e["total"] = "20.0"
    assert "wrong_type:total" in validate_event(e, RULES)