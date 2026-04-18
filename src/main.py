"""
Drive Organizer AI - Main Entry Point
Scalable Google Drive file organizer with local AI classification.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .auth import GoogleAuthManager
from .file_extractor import FileExtractor
from .classifier import AIClassifier
from .drive_manager import DriveManager
from .config import Config
from .reporter import OrganizationReporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("organizer.log"),
    ],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Drive Organizer AI - Automatically categorize your Google Drive"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate organization without moving files",
    )
    parser.add_argument(
        "--folder-id",
        type=str,
        default=None,
        help="Specific Drive folder ID to organize (default: root)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of files to process per batch (default: 20)",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Restrict to specific categories (e.g. HR Finance)",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.6,
        help="Minimum confidence score to move a file (0.0-1.0, default: 0.6)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a detailed HTML report after organizing",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to custom configuration file",
    )
    return parser.parse_args()


async def main(args: argparse.Namespace) -> None:
    logger.info("🧠 Drive Organizer AI starting up...")

    config = Config.load(args.config)
    if args.categories:
        config.allowed_categories = args.categories
    if args.confidence_threshold:
        config.confidence_threshold = args.confidence_threshold

    auth_manager = GoogleAuthManager(config)
    service = await auth_manager.get_service()

    classifier = AIClassifier(config)
    extractor = FileExtractor(config)
    drive_manager = DriveManager(service, config, dry_run=args.dry_run)
    reporter = OrganizationReporter()

    if args.dry_run:
        logger.info("🔍 DRY RUN mode — no files will be moved")

    folder_id = args.folder_id or "root"
    logger.info(f"📂 Scanning folder: {folder_id}")

    all_files = await drive_manager.list_files(folder_id=folder_id)
    logger.info(f"📄 Found {len(all_files)} files to process")

    results = []
    batches = [
        all_files[i : i + args.batch_size]
        for i in range(0, len(all_files), args.batch_size)
    ]

    for batch_num, batch in enumerate(batches, 1):
        logger.info(f"⚙️  Processing batch {batch_num}/{len(batches)} ({len(batch)} files)")
        batch_results = await process_batch(
            batch, extractor, classifier, drive_manager, config
        )
        results.extend(batch_results)

    moved = sum(1 for r in results if r.get("moved"))
    skipped = sum(1 for r in results if not r.get("moved"))
    logger.info(
        f"✅ Done! Moved: {moved} | Skipped/Low-confidence: {skipped} | Total: {len(results)}"
    )

    if args.report:
        report_path = reporter.generate(results)
        logger.info(f"📊 Report saved to: {report_path}")


async def process_batch(batch, extractor, classifier, drive_manager, config) -> list:
    tasks = [
        process_single_file(f, extractor, classifier, drive_manager, config)
        for f in batch
    ]
    return await asyncio.gather(*tasks, return_exceptions=False)


async def process_single_file(
    file_meta: dict,
    extractor: "FileExtractor",
    classifier: "AIClassifier",
    drive_manager: "DriveManager",
    config: "Config",
) -> dict:
    file_id = file_meta["id"]
    file_name = file_meta.get("name", "unknown")
    mime_type = file_meta.get("mimeType", "")

    try:
        content = await extractor.extract(file_id, file_name, mime_type)
        result = classifier.classify(file_name, content, mime_type)

        if result.confidence >= config.confidence_threshold:
            moved = await drive_manager.move_to_category(
                file_id, file_name, result.category
            )
            return {
                "file": file_name,
                "category": result.category,
                "confidence": result.confidence,
                "moved": moved,
                "reason": result.reason,
            }
        else:
            logger.warning(
                f"⚠️  Low confidence ({result.confidence:.2f}) for '{file_name}' → '{result.category}' — skipping"
            )
            return {
                "file": file_name,
                "category": result.category,
                "confidence": result.confidence,
                "moved": False,
                "reason": "Below confidence threshold",
            }

    except Exception as e:
        logger.error(f"❌ Failed to process '{file_name}': {e}")
        return {"file": file_name, "category": None, "moved": False, "reason": str(e)}


def run():
    args = parse_args()
    asyncio.run(main(args))


if __name__ == "__main__":
    run()
