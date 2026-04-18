"""
Google Drive folder and file operations manager.
Handles folder creation, file moving, and listing with pagination.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from googleapiclient.errors import HttpError

from .config import Config

logger = logging.getLogger(__name__)


class DriveManager:
    """
    Manages Google Drive folder structure and file operations.

    Folder cache prevents redundant API calls — once a category folder
    is created or found, its ID is stored for the session lifetime.
    """

    def __init__(self, service, config: Config, dry_run: bool = False):
        self.service = service
        self.config = config
        self.dry_run = dry_run
        self._folder_cache: Dict[str, str] = {}
        self._root_folder_id: Optional[str] = None

    async def list_files(
        self,
        folder_id: str = "root",
        page_size: int = 100,
    ) -> List[dict]:
        """List all files in a Drive folder (recursively follows subfolders)."""
        loop = asyncio.get_event_loop()
        all_files = []
        page_token = None

        while True:
            def _page(token=page_token):
                query = (
                    f"'{folder_id}' in parents "
                    "and trashed = false "
                    "and mimeType != 'application/vnd.google-apps.folder'"
                )
                kwargs = dict(
                    q=query,
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                )
                if token:
                    kwargs["pageToken"] = token
                return self.service.files().list(**kwargs).execute()

            result = await loop.run_in_executor(None, _page)
            files = result.get("files", [])
            all_files.extend(files)
            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return all_files

    async def move_to_category(
        self, file_id: str, file_name: str, category: str
    ) -> bool:
        """Move a file into its category subfolder under the root organizer folder."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would move '{file_name}' → {category}/")
            return True

        try:
            root_id = await self._get_or_create_root_folder()
            cat_id = await self._get_or_create_category_folder(root_id, category)
            await self._move_file(file_id, cat_id)
            logger.info(f"✅ Moved '{file_name}' → {self.config.root_folder_name}/{category}/")
            return True
        except HttpError as e:
            logger.error(f"❌ Drive API error moving '{file_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error moving '{file_name}': {e}")
            return False

    async def _get_or_create_root_folder(self) -> str:
        if self._root_folder_id:
            return self._root_folder_id
        folder_id = await self._find_or_create_folder(
            self.config.root_folder_name, parent_id=None
        )
        self._root_folder_id = folder_id
        return folder_id

    async def _get_or_create_category_folder(self, root_id: str, category: str) -> str:
        cache_key = f"{root_id}/{category}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        folder_id = await self._find_or_create_folder(category, parent_id=root_id)
        self._folder_cache[cache_key] = folder_id
        return folder_id

    async def _find_or_create_folder(
        self, name: str, parent_id: Optional[str]
    ) -> str:
        loop = asyncio.get_event_loop()

        def _search():
            q = (
                f"name='{name}' "
                "and mimeType='application/vnd.google-apps.folder' "
                "and trashed=false"
            )
            if parent_id:
                q += f" and '{parent_id}' in parents"
            result = (
                self.service.files()
                .list(q=q, fields="files(id, name)", pageSize=1)
                .execute()
            )
            return result.get("files", [])

        existing = await loop.run_in_executor(None, _search)
        if existing:
            return existing[0]["id"]

        def _create():
            meta = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                meta["parents"] = [parent_id]
            folder = (
                self.service.files()
                .create(body=meta, fields="id")
                .execute()
            )
            return folder["id"]

        folder_id = await loop.run_in_executor(None, _create)
        logger.info(f"📁 Created folder: {name} (id={folder_id})")
        return folder_id

    async def _move_file(self, file_id: str, target_folder_id: str) -> None:
        loop = asyncio.get_event_loop()

        def _get_parents():
            f = (
                self.service.files()
                .get(fileId=file_id, fields="parents")
                .execute()
            )
            return ",".join(f.get("parents", []))

        current_parents = await loop.run_in_executor(None, _get_parents)

        def _update():
            self.service.files().update(
                fileId=file_id,
                addParents=target_folder_id,
                removeParents=current_parents,
                fields="id, parents",
            ).execute()

        await loop.run_in_executor(None, _update)
