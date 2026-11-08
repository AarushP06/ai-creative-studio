"""Validation pipeline: raw model text → JSON → Pydantic → business rules.

The model proposes. This code decides.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from app.models import ServiceCard
from app.rules import validate_business_rules


@dataclass
class PipelineResult:
    accepted: bool
    card: ServiceCard | None = None
    violations: list[str] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)

    def step(self, name: str, ok: bool, detail: str = "") -> None:
        self.trace.append({"step": name, "ok": ok, "detail": detail})


def _pydantic_messages(err: ValidationError) -> list[str]:
    messages = []
    for e in err.errors():
        location = ".".join(str(p) for p in e["loc"]) or "card"
        messages.append(f"{location}: {e['msg']}")
    return messages


def validate_raw_output(raw_text: str) -> PipelineResult:
    result = PipelineResult(accepted=False)

    # 1. Is it JSON at all?
    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        result.violations = ["response is not valid JSON"]
        result.step("parse JSON", False, "not JSON")
        return result
    if not isinstance(data, dict):
        result.violations = ["response must be a JSON object"]
        result.step("parse JSON", False, "not an object")
        return result
    result.step("parse JSON", True)

    # 2. Does it match the contract? (types, lengths, allowed values, no extra fields)
    try:
        card = ServiceCard.model_validate(data)
    except ValidationError as err:
        result.violations = _pydantic_messages(err)
        result.step("Pydantic schema", False, f"{len(result.violations)} problem(s)")
        return result
    result.step("Pydantic schema", True)

    # 3. Does it follow the business rules?
    violations = validate_business_rules(card)
    if violations:
        result.violations = violations
        result.step("business rules", False, f"{len(violations)} problem(s)")
        return result
    result.step("business rules", True)

    result.accepted = True
    result.card = card
    return result
