"""
Organization report generator.
Produces a clean HTML report summarizing what was moved, what was skipped, and why.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List

from .config import Config

logger = logging.getLogger(__name__)


class OrganizationReporter:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, results: List[dict]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"report_{timestamp}.html"

        moved = [r for r in results if r.get("moved")]
        skipped = [r for r in results if not r.get("moved")]
        category_counts = Counter(r["category"] for r in moved if r.get("category"))

        html = self._render_html(results, moved, skipped, category_counts, timestamp)
        with open(report_path, "w") as f:
            f.write(html)

        json_path = self.output_dir / f"report_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"📊 Report generated: {report_path}")
        return str(report_path)

    def _render_html(self, results, moved, skipped, category_counts, timestamp) -> str:
        category_rows = "".join(
            f"<tr><td>{cat}</td><td>{count}</td></tr>"
            for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])
        )
        file_rows = "".join(
            f"""<tr>
                <td>{r.get('file','')}</td>
                <td><span class="badge {'moved' if r.get('moved') else 'skipped'}">{r.get('category','—')}</span></td>
                <td>{r.get('confidence', 0):.0%}</td>
                <td>{'✅' if r.get('moved') else '⚠️'}</td>
                <td>{r.get('reason','')}</td>
            </tr>"""
            for r in results
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Drive Organizer Report — {timestamp}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 960px; margin: 40px auto; padding: 0 24px; color: #1a1a1a; }}
  h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 4px; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 32px; }}
  .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 32px; }}
  .stat-card {{ background: #f8f8f8; border-radius: 12px; padding: 20px; }}
  .stat-card .num {{ font-size: 2.2rem; font-weight: 700; color: #2563eb; }}
  .stat-card .label {{ font-size: 0.85rem; color: #555; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 32px; font-size: 0.9rem; }}
  th {{ background: #f0f0f0; padding: 10px 12px; text-align: left; font-weight: 600; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.8rem; font-weight: 500; }}
  .badge.moved {{ background: #dcfce7; color: #166534; }}
  .badge.skipped {{ background: #fef9c3; color: #713f12; }}
  h2 {{ font-size: 1.1rem; font-weight: 600; margin: 32px 0 12px; }}
</style>
</head>
<body>
<h1>🧠 Drive Organizer Report</h1>
<p class="meta">Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<div class="stats">
  <div class="stat-card"><div class="num">{len(results)}</div><div class="label">Total files</div></div>
  <div class="stat-card"><div class="num">{len(moved)}</div><div class="label">Files moved</div></div>
  <div class="stat-card"><div class="num">{len(skipped)}</div><div class="label">Skipped</div></div>
</div>
<h2>By Category</h2>
<table>
  <thead><tr><th>Category</th><th>Files Moved</th></tr></thead>
  <tbody>{category_rows}</tbody>
</table>
<h2>All Files</h2>
<table>
  <thead><tr><th>File</th><th>Category</th><th>Confidence</th><th>Status</th><th>Reason</th></tr></thead>
  <tbody>{file_rows}</tbody>
</table>
</body>
</html>"""
