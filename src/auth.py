"""
Google OAuth2 authentication manager.
Handles token lifecycle: creation, refresh, and secure pickle storage.
"""

import asyncio
import logging
import os
import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import Config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleAuthManager:
    """
    Manages Google OAuth2 credentials with automatic refresh.

    Credentials are cached locally in a pickle file for subsequent runs.
    Token refresh happens transparently if the access token has expired.
    """

    def __init__(self, config: Config):
        self.config = config
        self._credentials: Optional[Credentials] = None

    async def get_service(self):
        """Return an authenticated Google Drive API service."""
        credentials = await self._get_credentials()
        loop = asyncio.get_event_loop()
        service = await loop.run_in_executor(
            None, lambda: build("drive", "v3", credentials=credentials)
        )
        logger.info("✅ Google Drive API service ready")
        return service

    async def _get_credentials(self) -> Credentials:
        """Load, refresh, or create OAuth2 credentials."""
        if self._credentials and self._credentials.valid:
            return self._credentials

        credentials = self._load_token()

        if credentials and credentials.expired and credentials.refresh_token:
            logger.info("🔄 Refreshing expired token...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: credentials.refresh(Request()))
            self._save_token(credentials)

        if not credentials or not credentials.valid:
            credentials = await self._run_oauth_flow()

        self._credentials = credentials
        return credentials

    def _load_token(self) -> Optional[Credentials]:
        token_path = Path(self.config.token_path)
        if token_path.exists():
            try:
                with open(token_path, "rb") as f:
                    creds = pickle.load(f)
                logger.info(f"🔑 Loaded token from {token_path}")
                return creds
            except Exception as e:
                logger.warning(f"⚠️  Could not load token: {e}")
        return None

    def _save_token(self, credentials: Credentials) -> None:
        token_path = Path(self.config.token_path)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "wb") as f:
            pickle.dump(credentials, f)
        logger.info(f"💾 Token saved to {token_path}")

    async def _run_oauth_flow(self) -> Credentials:
        """Launch browser-based OAuth2 flow."""
        credentials_path = Path(self.config.credentials_path)
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"credentials.json not found at {credentials_path}. "
                "Download it from Google Cloud Console → Credentials → OAuth Client ID."
            )
        logger.info("🌐 Opening browser for Google OAuth login...")
        loop = asyncio.get_event_loop()
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        credentials = await loop.run_in_executor(
            None, lambda: flow.run_local_server(port=0)
        )
        self._save_token(credentials)
        return credentials

    def revoke(self) -> None:
        """Revoke the stored token and delete local cache."""
        token_path = Path(self.config.token_path)
        if token_path.exists():
            token_path.unlink()
            logger.info("🗑️  Token revoked and deleted")
        self._credentials = None
