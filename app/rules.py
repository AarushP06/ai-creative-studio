"""Layer 2 of validation: business rules that a JSON schema cannot express.

Each check returns a list of human-readable violations (empty list = OK).
A card is shown on the website only when Pydantic AND every rule here pass.

Note: these rules check format and banned content. They do NOT prove that a
claim is true — that is a separate, harder problem (see docs/ARCHITECTURE.md).
"""
from __future__ import annotations

import re

from app.models import TEXT_FIELDS, ServiceCard

# Money: $19, $ 19, 19$, 19 $, 4,50 $, 25 dollars, 30 CAD, €10, £10
PRICE_PATTERN = re.compile(
    r"(\$\s?\d)|(\d[\d.,]*\s?\$)|(\b\d[\d.,]*\s?(dollars?|bucks|cad|usd|eur)\b)|[€£]",
    re.IGNORECASE,
)

GUARANTEE_PATTERN = re.compile(
    r"\b(guarantee[ds]?|100\s?%|risk[- ]free|best in (town|the city|canada|the world)|#1)",
    re.IGNORECASE,
)


def check_no_prices(card: ServiceCard) -> list[str]:
    """Brand rule: no prices or amounts of money anywhere on a card."""
    violations = []
    for field in TEXT_FIELDS:
        if PRICE_PATTERN.search(getattr(card, field)):
            violations.append(f"{field}: contains a price — prices are not allowed on cards")
    return violations


def check_no_guarantees(card: ServiceCard) -> list[str]:
    """Brand rule: no guarantees or absolute claims anywhere on a card."""
    violations = []
    for field in TEXT_FIELDS:
        text = getattr(card, field)
        if GUARANTEE_PATTERN.search(text):
            violations.append(f"{field}: contains a guarantee or absolute claim")
    return violations


# Every rule the application enforces. Add new checks here.
RULES = [
    check_no_prices,
    check_no_guarantees,
]


def validate_business_rules(card: ServiceCard) -> list[str]:
    violations: list[str] = []
    for rule in RULES:
        violations.extend(rule(card))
    return violations
