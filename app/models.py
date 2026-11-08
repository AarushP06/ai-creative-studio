"""The contract for one AI-generated service card.

Layer 1 of validation: Pydantic checks fields, types, lengths and allowed values.
Layer 2 (app/rules.py) checks business rules such as "no prices".

Why both? Gemini's structured output enforces the enum lists, but it IGNORES
maxLength. Syntactically valid JSON can still break our page or our brand.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Keep these in sync with brand/brand-rules.json (tests/test_models.py checks it).
TITLE_MAX = 60
SUMMARY_MIN = 20
SUMMARY_MAX = 160
CTA_TEXT_MAX = 30

ImageName = Literal["workspace", "growth", "community", "craft"]
Tone = Literal["friendly", "professional", "bold"]
CtaAction = Literal["book", "contact", "visit"]

# Free-text fields written by the model. Every business rule must scan ALL of them.
TEXT_FIELDS = ("title", "summary", "cta_text")


class ServiceCard(BaseModel):
    """One card on the website. Free text + controlled options."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Free text — Gemini really writes these.
    title: str = Field(min_length=3, max_length=TITLE_MAX)
    summary: str = Field(min_length=SUMMARY_MIN, max_length=SUMMARY_MAX)
    cta_text: str = Field(min_length=2, max_length=CTA_TEXT_MAX)

    # Controlled options — Gemini may only choose from these lists.
    image: ImageName
    tone: Tone
    cta_action: CtaAction


def gemini_response_schema() -> dict:
    """JSON Schema sent to Gemini with the request.

    We send the full schema, including maxLength. Gemini enforces the enums
    but ignores maxLength — which is exactly why ServiceCard re-checks everything.
    """
    schema = ServiceCard.model_json_schema()
    schema.pop("title", None)
    return schema
