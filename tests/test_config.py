"""Tests for the Config module."""

import pytest
from src.config import Config


def test_default_config():
    config = Config()
    assert config.confidence_threshold == 0.6
    assert config.batch_size == 20
    assert "HR" in config.allowed_categories
    assert "Finance" in config.allowed_categories


def test_config_has_all_categories():
    config = Config()
    expected = ["HR", "Finance", "Academics", "Projects", "Marketing", "Personal"]
    for cat in expected:
        assert cat in config.allowed_categories


def test_load_missing_file_uses_defaults():
    config = Config.load("nonexistent_config.yaml")
    assert config.confidence_threshold == 0.6
