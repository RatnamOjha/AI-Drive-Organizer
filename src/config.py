"""
Configuration management for Drive Organizer AI.
Supports YAML config files and environment variable overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


DEFAULT_CATEGORIES = [
    "HR",
    "Finance",
    "Academics",
    "Projects",
    "Marketing",
    "Personal",
    "Legal",
    "Technical",
    "Miscellaneous",
]


@dataclass
class Config:
    # Auth
    credentials_path: str = "credentials/credentials.json"
    token_path: str = "credentials/token.pickle"

    # Classification
    allowed_categories: List[str] = field(default_factory=lambda: list(DEFAULT_CATEGORIES))
    confidence_threshold: float = 0.6
    keywords_path: str = "assets/category_keywords.json"

    # Drive
    root_folder_name: str = "Organized"
    batch_size: int = 20
    max_content_chars: int = 3000

    # Extraction
    ocr_enabled: bool = True
    tesseract_path: Optional[str] = None

    # Reporting
    report_output_dir: str = "reports"

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        """Load config from YAML file, falling back to defaults."""
        instance = cls()
        config_file = Path(config_path)

        if config_file.exists() and HAS_YAML:
            with open(config_file) as f:
                data = yaml.safe_load(f) or {}
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

        # Environment variable overrides
        env_map = {
            "DRIVE_ORGANIZER_CREDENTIALS": "credentials_path",
            "DRIVE_ORGANIZER_TOKEN": "token_path",
            "DRIVE_ORGANIZER_THRESHOLD": "confidence_threshold",
        }
        for env_key, attr in env_map.items():
            val = os.environ.get(env_key)
            if val is not None:
                attr_type = type(getattr(instance, attr))
                setattr(instance, attr, attr_type(val))

        return instance

    def to_yaml(self) -> str:
        if not HAS_YAML:
            raise RuntimeError("PyYAML not installed")
        return yaml.dump(self.__dict__, default_flow_style=False)
