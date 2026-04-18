"""Tests for the AI classifier module."""

import pytest
from src.classifier import AIClassifier
from src.config import Config


@pytest.fixture
def classifier():
    config = Config()
    config.keywords_path = "assets/category_keywords.json"
    return AIClassifier(config)


def test_finance_invoice(classifier):
    result = classifier.classify("Q3_invoice_2024.pdf", "Invoice total $5000 payment due")
    assert result.category == "Finance"
    assert result.confidence > 0.3


def test_hr_resume(classifier):
    result = classifier.classify("John_Resume.pdf", "Work experience skills education CV")
    assert result.category == "HR"
    assert result.confidence > 0.3


def test_legal_nda(classifier):
    result = classifier.classify("NDA_Agreement.pdf", "Non-disclosure agreement confidentiality clause liability")
    assert result.category == "Legal"
    assert result.confidence > 0.3


def test_low_confidence_misc(classifier):
    result = classifier.classify("untitled", "")
    assert result.confidence < 0.5 or result.category == "Miscellaneous"


def test_confidence_range(classifier):
    result = classifier.classify("any_file.txt", "some generic content here")
    assert 0.0 <= result.confidence <= 1.0


def test_all_categories_scored(classifier):
    result = classifier.classify("invoice.pdf", "budget finance payment tax receipt")
    assert len(result.scores) > 0


def test_technical_api(classifier):
    result = classifier.classify("README.md", "API documentation docker deployment kubernetes ci cd")
    assert result.category == "Technical"
