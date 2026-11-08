"""Layer 2: business rules a JSON schema cannot express."""
import pytest

from app.models import ServiceCard
from app.rules import validate_business_rules
from tests.conftest import VALID_CARD, card


def violations(data: dict) -> list[str]:
    return validate_business_rules(ServiceCard.model_validate(data))


def test_clean_card_has_no_violations():
    assert violations(VALID_CARD) == []


@pytest.mark.parametrize(
    "summary",
    [
        "Specialty coffee and pastries, now only $4 for students every afternoon.",
        "Specialty coffee and pastries, now only 4,50 $ for students every afternoon.",
        "Our study room costs 25 dollars per hour, coffee included for the group.",
    ],
)
def test_price_in_summary_is_rejected(summary):
    assert any("price" in v for v in violations(card(summary=summary)))


def test_price_in_title_is_rejected():
    # Regression test added with the fix for Issue #1.
    assert any("price" in v for v in violations(card(title="Tune-ups from 25 $ this week")))


def test_price_in_cta_text_is_rejected():
    # Issue #1: a price on the button reached the website.
    assert any("price" in v for v in violations(card(cta_text="Only $19 a day!")))


@pytest.mark.parametrize("field", ["title", "summary", "cta_text"])
def test_guarantee_is_rejected_in_every_text_field(field):
    text = {"title": "Guaranteed great coffee",
            "summary": "The best in town for study sessions, quiet tables and fresh pastries.",
            "cta_text": "Risk-free visit"}[field]
    assert any("guarantee" in v for v in violations(card(**{field: text})))


def test_numbers_that_are_not_prices_are_allowed():
    ok = card(summary="Open every day from 7 to 21, with 12 quiet tables and 2 meeting rooms.")
    assert violations(ok) == []
