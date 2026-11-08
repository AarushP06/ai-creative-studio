"""Layer 1: the Pydantic contract (types, lengths, allowed values, no extra fields)."""
import json

import pytest
from pydantic import ValidationError
from typing import get_args

from app import models
from app.config import BRAND_RULES_PATH
from app.models import ServiceCard
from tests.conftest import VALID_CARD, card


def test_valid_card_is_accepted():
    assert ServiceCard.model_validate(VALID_CARD).title == VALID_CARD["title"]


@pytest.mark.parametrize(
    "bad",
    [
        card(title="x" * 61),                      # too long
        card(summary="Too short."),                # too short
        card(cta_text="Click here to book your table now"),  # > 30 chars
        card(image="rocket-ship"),                 # not an allowed image
        card(tone="angry"),                        # not an allowed tone
        card(cta_action="buy"),                    # not an allowed action
        card(discount_code="FREE"),                # extra field
        {k: v for k, v in VALID_CARD.items() if k != "summary"},  # missing field
    ],
)
def test_invalid_cards_are_rejected(bad):
    with pytest.raises(ValidationError):
        ServiceCard.model_validate(bad)


def test_contract_matches_brand_rules_file():
    """brand/brand-rules.json is the single source of truth — code must agree with it."""
    rules = json.loads(BRAND_RULES_PATH.read_text(encoding="utf-8"))
    limits, allowed = rules["card_limits"], rules["allowed_values"]
    assert models.TITLE_MAX == limits["title_max_chars"]
    assert models.SUMMARY_MIN == limits["summary_min_chars"]
    assert models.SUMMARY_MAX == limits["summary_max_chars"]
    assert models.CTA_TEXT_MAX == limits["cta_text_max_chars"]
    assert list(get_args(models.ImageName)) == allowed["image"]
    assert list(get_args(models.Tone)) == allowed["tone"]
    assert list(get_args(models.CtaAction)) == allowed["cta_action"]


def test_schema_sent_to_gemini_has_enums_and_no_extra_fields():
    schema = models.gemini_response_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(VALID_CARD)
    assert "enum" in schema["properties"]["image"] or "$ref" in json.dumps(schema["properties"]["image"])
