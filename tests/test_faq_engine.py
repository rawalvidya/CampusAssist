
import json
from pathlib import Path

import pytest

from faq_engine import FAQEngine, normalize_text


FAQ_FILE = Path(__file__).resolve().parent.parent / "faqs.json"


def test_faq_file_contains_valid_questions():
    with FAQ_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data


def test_normalize_text_handles_uppercase_and_spaces():
    assert normalize_text("  HELLO   WORLD ") == "hello world"


def test_faq_engine_loads_faqs():
    engine = FAQEngine()

    assert engine.faqs


def test_known_faq_returns_an_answer():
    engine = FAQEngine()
    question = engine.faqs[0]["question"]

    result = engine.search(question)

    assert result is not None
    assert result["answer"]


def test_empty_question_returns_no_match():
    engine = FAQEngine()

    assert engine.search("") is None


def test_answer_method_returns_text():
    engine = FAQEngine()
    question = engine.faqs[0]["question"]

    result = engine.answer(question)

    assert isinstance(result, str)
    assert result.strip()
