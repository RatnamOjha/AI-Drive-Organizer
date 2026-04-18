# 🧠 Drive Organizer AI

> **Automatically categorize and organize your Google Drive files using on-device AI — no manual sorting, no cloud APIs, no privacy trade-offs.**

![CI](https://github.com/your-username/drive-organizer-ai/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Google Drive API](https://img.shields.io/badge/Google%20Drive-API-green)
![License](https://img.shields.io/badge/License-MIT-purple)
![Local AI](https://img.shields.io/badge/AI-Offline--First-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)

Say goodbye to digital clutter. This tool scans your Google Drive, extracts text from **PDFs, Docs, Sheets, Images (via OCR)**, and intelligently moves files into categories using a **TF-IDF weighted classifier** — with confidence scoring, dry-run mode, batch processing, and full HTML reports.

All processing happens **locally** — your data never leaves your machine.

---

## 🌐 Live Demo

👉 **[View landing page](https://your-username.github.io/drive-organizer-ai)**

---

## 🏗️ Architecture

```
google-drive/
      │
      ▼
┌─────────────┐    batch/async    ┌──────────────────┐
│ DriveManager│ ────────────────► │  FileExtractor   │
│ list_files  │                   │  PDF/DOCX/OCR/   │
└─────────────┘                   │  XLSX/GDocs      │
                                  └────────┬─────────┘
                                           │ text content
                                           ▼
                                  ┌──────────────────┐
                                  │  AIClassifier    │
                                  │  TF-IDF + weights│
                                  │  confidence score│
                                  └────────┬─────────┘
                                           │ category + confidence
                                           ▼
                                  ┌──────────────────┐     ┌──────────────┐
                                  │  DriveManager    │ ──► │  Reporter    │
                                  │  move_to_category│     │  HTML + JSON │
                                  └──────────────────┘     └──────────────┘
```

## 📂 Project Structure

```
drive-organizer-ai/
├── src/
│   ├── __init__.py
│   ├── main.py            # Entry point + async orchestration
│   ├── auth.py            # Google OAuth2 with token refresh
│   ├── config.py          # YAML + env var config management
│   ├── file_extractor.py  # Multi-format async text extraction
│   ├── classifier.py      # TF-IDF weighted AI classifier
│   ├── drive_manager.py   # Folder management + file moves
│   └── reporter.py        # HTML + JSON report generator
├── assets/
│   └── category_keywords.json   # Customizable weighted keywords
├── tests/
│   ├── test_classifier.py
│   └── test_config.py
├── docs/
│   └── index.html               # GitHub Pages landing page
├── .github/
│   └── workflows/
│       └── ci.yml               # 5-stage CI/CD pipeline
├── credentials/                 # (git-ignored) OAuth credentials
├── config.example.yaml          # Example configuration
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### 1. Set up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project → Enable **Google Drive API**
3. Under **Credentials** → Create **OAuth Client ID** → Desktop App
4. Download JSON → save as `credentials/credentials.json`

> ⚠️ Never commit `credentials.json`! It's excluded via `.gitignore`.

### 2. Clone & Install

```bash
git clone https://github.com/your-username/drive-organizer-ai.git
cd drive-organizer-ai

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
```

### 3. Configure

```bash
cp config.example.yaml config.yaml
# Edit config.yaml to adjust categories, confidence threshold, etc.
```

### 4. Run

```bash
# Safe: preview what WOULD happen (no files moved)
python -m src.main --dry-run --report

# Organize specific categories with custom confidence
python -m src.main --categories HR Finance Legal --confidence-threshold 0.75

# Full run with report
python -m src.main --report

# Docker
docker run -v $(pwd)/credentials:/app/credentials \
           -v $(pwd)/reports:/app/reports \
           ghcr.io/your-username/drive-organizer-ai
```

---

## 🎛️ CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--dry-run` | off | Simulate without moving files |
| `--folder-id` | `root` | Drive folder ID to organize |
| `--batch-size` | `20` | Files processed concurrently |
| `--categories` | all | Restrict to specific categories |
| `--confidence-threshold` | `0.6` | Min score to move (0.0–1.0) |
| `--report` | off | Generate HTML + JSON report |
| `--config` | `config.yaml` | Custom config file path |

---

## 🧠 How the Classifier Works

The classifier uses **TF-IDF scoring** with hand-tuned keyword weights:

1. File name + extracted content are normalized (lowercase, punctuation stripped)
2. For each category, every keyword is matched against the token set
3. Score = `term_frequency × IDF × keyword_weight`
4. Scores are normalized across all categories → confidence (0–1)
5. Files below `confidence_threshold` are skipped (not force-categorized)

**Customize keywords** in `assets/category_keywords.json`:
```json
{
  "Finance": [
    {"term": "invoice", "weight": 3.0},
    {"term": "my-custom-term", "weight": 2.5}
  ]
}
```

---

## 🔒 Privacy & Security

| Feature | Status |
|---------|--------|
| External data transfer | ❌ None — all NLP is local |
| Token storage | Local `token.pickle` only |
| Open source | ✅ Fully auditable |
| Permissions | Drive read + move only |
| Docker non-root user | ✅ Runs as `organizer` (uid 1000) |

---

## ⚙️ CI/CD Pipeline

Every push to `main` triggers a 5-stage GitHub Actions pipeline:

```
Lint (Ruff + Black)
    ↓
Test (pytest, Python 3.9 / 3.10 / 3.11 + coverage)
    ↓
Security (Bandit)
    ↓
Docker (build + push to GHCR)
    ↓
Deploy (GitHub Pages)
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Write tests for new behavior
4. Open a pull request against `main`

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.
