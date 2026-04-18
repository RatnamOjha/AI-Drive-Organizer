"""
AI-powered file classifier using local keyword + TF-IDF scoring.
No external API calls — all inference happens on-device.
"""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reason: str
    scores: Dict[str, float]


class AIClassifier:
    """
    Keyword-weighted TF-IDF classifier for Drive file categorization.

    For each category, a keyword list (with optional weights) is loaded from
    `category_keywords.json`. The classifier computes a weighted term-frequency
    score for each category and normalises to produce confidence values.
    """

    def __init__(self, config: Config):
        self.config = config
        self.keywords: Dict[str, List[Tuple[str, float]]] = {}
        self._load_keywords()

    def _load_keywords(self) -> None:
        kw_path = Path(self.config.keywords_path)
        if not kw_path.exists():
            logger.warning(f"⚠️  Keywords file not found: {kw_path}. Using built-in defaults.")
            self.keywords = self._default_keywords()
            return

        with open(kw_path) as f:
            raw = json.load(f)

        for category, entries in raw.items():
            if category not in self.config.allowed_categories:
                continue
            parsed = []
            for entry in entries:
                if isinstance(entry, str):
                    parsed.append((entry.lower(), 1.0))
                elif isinstance(entry, dict):
                    term = entry.get("term", "").lower()
                    weight = float(entry.get("weight", 1.0))
                    if term:
                        parsed.append((term, weight))
            self.keywords[category] = parsed

        missing = [c for c in self.config.allowed_categories if c not in self.keywords]
        if missing:
            defaults = self._default_keywords()
            for cat in missing:
                if cat in defaults:
                    self.keywords[cat] = defaults[cat]

        logger.info(f"📚 Loaded keywords for {len(self.keywords)} categories")

    def classify(self, file_name: str, content: str, mime_type: str = "") -> ClassificationResult:
        """Classify a file, returning category + confidence + reasoning."""
        text = self._normalize(f"{file_name} {content}")
        tokens = text.split()
        token_set = set(tokens)

        scores: Dict[str, float] = {}

        for category, keyword_pairs in self.keywords.items():
            score = 0.0
            matched_terms = []
            for term, weight in keyword_pairs:
                term_tokens = term.split()
                if len(term_tokens) == 1:
                    if term in token_set:
                        tf = tokens.count(term) / max(len(tokens), 1)
                        idf = math.log(1 + 1 / (keyword_pairs.index((term, weight)) + 1))
                        score += tf * idf * weight
                        matched_terms.append(term)
                else:
                    if all(t in token_set for t in term_tokens):
                        score += 0.5 * weight
                        matched_terms.append(term)
            scores[category] = score

        if not scores or max(scores.values()) == 0:
            return ClassificationResult(
                category="Miscellaneous",
                confidence=0.0,
                reason="No keyword matches found",
                scores=scores,
            )

        total = sum(scores.values())
        normalized = {k: v / total for k, v in scores.items()}

        best_category = max(normalized, key=normalized.get)
        confidence = normalized[best_category]

        matched = [
            term for term, _ in self.keywords.get(best_category, [])
            if term in text
        ][:5]
        reason = (
            f"Matched terms: {', '.join(matched)}" if matched else "Keyword pattern match"
        )

        return ClassificationResult(
            category=best_category,
            confidence=round(confidence, 4),
            reason=reason,
            scores={k: round(v, 4) for k, v in normalized.items()},
        )

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _default_keywords() -> Dict[str, List[Tuple[str, float]]]:
        return {
            "HR": [
                ("resume", 2.0), ("cv", 1.5), ("employee", 1.5), ("onboarding", 2.0),
                ("payroll", 2.0), ("leave", 1.0), ("interview", 1.5), ("recruitment", 2.0),
                ("performance review", 2.0), ("offer letter", 2.5), ("benefits", 1.0),
                ("policy", 1.0), ("handbook", 1.5), ("appraisal", 2.0),
            ],
            "Finance": [
                ("invoice", 2.5), ("receipt", 2.0), ("budget", 2.0), ("tax", 2.0),
                ("financial", 1.5), ("expense", 2.0), ("revenue", 1.5), ("profit", 1.5),
                ("loss", 1.0), ("balance sheet", 2.5), ("income statement", 2.5),
                ("audit", 2.0), ("payment", 1.5), ("bank", 1.5), ("ledger", 2.0),
            ],
            "Academics": [
                ("thesis", 2.5), ("research", 1.5), ("paper", 1.0), ("study", 1.0),
                ("assignment", 2.0), ("homework", 2.0), ("exam", 2.0), ("course", 1.5),
                ("lecture", 2.0), ("university", 1.5), ("college", 1.5), ("grade", 1.5),
                ("syllabus", 2.5), ("bibliography", 2.0), ("abstract", 1.5),
            ],
            "Projects": [
                ("project", 1.5), ("sprint", 2.0), ("milestone", 2.0), ("deadline", 2.0),
                ("roadmap", 2.5), ("requirement", 1.5), ("specification", 2.0),
                ("jira", 2.0), ("kanban", 2.0), ("agile", 2.0), ("backlog", 2.0),
                ("architecture", 1.5), ("design doc", 2.5),
            ],
            "Marketing": [
                ("campaign", 2.0), ("marketing", 2.0), ("brand", 1.5), ("seo", 2.5),
                ("social media", 2.0), ("advertisement", 2.0), ("content", 1.0),
                ("analytics", 1.5), ("conversion", 2.0), ("lead", 1.5), ("funnel", 2.0),
                ("copywriting", 2.5), ("press release", 2.5),
            ],
            "Personal": [
                ("personal", 1.5), ("diary", 2.5), ("journal", 2.0), ("family", 1.5),
                ("photo", 1.0), ("travel", 1.5), ("recipe", 2.0), ("birthday", 2.0),
                ("private", 2.0), ("note", 1.0), ("reminder", 1.5),
            ],
            "Legal": [
                ("contract", 2.5), ("agreement", 2.0), ("nda", 3.0), ("legal", 2.0),
                ("terms", 1.5), ("clause", 2.0), ("liability", 2.0), ("warranty", 2.0),
                ("compliance", 2.0), ("regulation", 2.0), ("gdpr", 3.0), ("lawsuit", 2.5),
            ],
            "Technical": [
                ("code", 1.5), ("api", 2.0), ("database", 2.0), ("server", 1.5),
                ("software", 1.5), ("algorithm", 2.0), ("documentation", 1.5),
                ("readme", 2.5), ("deployment", 2.0), ("docker", 2.5), ("kubernetes", 2.5),
                ("python", 1.5), ("javascript", 1.5), ("sql", 2.0),
            ],
            "Miscellaneous": [
                ("misc", 2.0), ("other", 1.0), ("general", 1.0), ("untitled", 2.0),
            ],
        }
