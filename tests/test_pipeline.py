"""The full validation pipeline: raw text → JSON → Pydantic → rules."""
import pytest

from app.pipeline import validate_raw_output
from tests.conftest import MOCK_CARDS, SIMULATED, VALID_CARD, raw


def test_valid_raw_output_is_accepted():
    result = validate_raw_output(raw(VALID_CARD))
    assert result.accepted and result.card.title == VALID_CARD["title"]
    assert [s["step"] for s in result.trace] == ["parse JSON", "Pydantic schema", "business rules"]


@pytest.mark.parametrize("text", ["Sure! Here is your card: ...", "", "[1, 2, 3]", "null"])
def test_non_json_or_wrong_shape_is_rejected(text):
    result = validate_raw_output(text)
    assert not result.accepted and result.violations


@pytest.mark.parametrize("path", sorted(SIMULATED.glob("*.json")), ids=lambda p: p.stem)
def test_every_simulated_bad_response_is_rejected(path):
    """Each file in data/simulated_responses/ is a deliberately invalid model output."""
    result = validate_raw_output(path.read_text(encoding="utf-8"))
    assert not result.accepted, f"{path.name} should be rejected but was accepted"


@pytest.mark.parametrize("path", sorted(MOCK_CARDS.glob("*.json")), ids=lambda p: p.stem)
def test_every_mock_card_is_valid(path):
    """Fallback cards go through the same validator — they must always pass."""
    assert validate_raw_output(path.read_text(encoding="utf-8")).accepted
