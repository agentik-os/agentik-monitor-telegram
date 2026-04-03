"""Bridge client for bot-to-dashboard communication via Convex HTTP endpoints."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ConvexBridge:
    """Async client that pushes bot events to the Convex dashboard."""

    def __init__(self, convex_site_url: str, api_secret: str) -> None:
        self._base_url = convex_site_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_secret}",
            "Content-Type": "application/json",
        }
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self._headers)

    async def _post(self, path: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST to Convex endpoint. Returns response JSON or None on error."""
        try:
            await self._ensure_session()
            url = f"{self._base_url}{path}"
            assert self._session is not None
            async with self._session.post(
                url, json=data, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("Bridge POST %s returned %s", path, resp.status)
                return None
        except Exception as e:
            logger.debug("Bridge POST %s failed: %s", path, e)
            return None

    async def _get(self, path: str) -> Optional[Dict[str, Any]]:
        """GET from Convex endpoint. Returns response JSON or None on error."""
        try:
            await self._ensure_session()
            url = f"{self._base_url}{path}"
            assert self._session is not None
            async with self._session.get(
                url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None

    def fire_and_forget(self, coro: Any) -> "asyncio.Task[Any]":
        """Schedule a coroutine without awaiting - for non-critical operations."""
        task = asyncio.create_task(coro)
        task.add_done_callback(
            lambda t: t.exception() if not t.cancelled() and t.exception() else None
        )
        return task

    # --- Heartbeat ---

    async def send_heartbeat(
        self,
        source: str = "telegram-bot",
        status: str = "healthy",
        metrics: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        data: Dict[str, Any] = {"source": source, "status": status}
        if metrics:
            data["metrics"] = metrics
        if message:
            data["message"] = message
        return await self._post("/api/heartbeat", data)

    # --- Notifications ---

    async def send_notification(
        self,
        title: str,
        message: str,
        source: str = "telegram-bot",
        type: str = "info",
    ) -> Optional[Dict[str, Any]]:
        return await self._post(
            "/api/notify",
            {"title": title, "message": message, "source": source, "type": type},
        )

    # --- Conversations ---

    async def upsert_conversation(
        self,
        telegram_chat_id: int,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        data: Dict[str, Any] = {"telegramChatId": telegram_chat_id}
        if title:
            data["title"] = title
        if metadata:
            data["metadata"] = metadata
        return await self._post("/api/conversation", data)

    async def send_message(
        self,
        telegram_chat_id: int,
        role: str,
        content: str,
        telegram_message_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        data: Dict[str, Any] = {
            "telegramChatId": telegram_chat_id,
            "role": role,
            "content": content,
        }
        if telegram_message_id:
            data["telegramMessageId"] = telegram_message_id
        if metadata:
            data["metadata"] = metadata
        return await self._post("/api/message", data)

    # --- Automations ---

    async def start_automation(
        self,
        name: str,
        type: str,
        triggered_by: str,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        data: Dict[str, Any] = {
            "name": name,
            "type": type,
            "triggeredBy": triggered_by,
        }
        if input_data:
            data["input"] = input_data
        return await self._post("/api/automation/start", data)

    async def complete_automation(
        self,
        execution_id: str,
        output: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        data: Dict[str, Any] = {"executionId": execution_id, "status": "completed"}
        if output:
            data["output"] = output
        return await self._post("/api/automation/complete", data)

    async def fail_automation(
        self, execution_id: str, error: str
    ) -> Optional[Dict[str, Any]]:
        return await self._post(
            "/api/automation/complete",
            {"executionId": execution_id, "status": "failed", "error": error},
        )

    # --- Activity Feed ---

    async def send_activity(
        self,
        type: str,
        title: str,
        description: Optional[str] = None,
        source: str = "telegram-bot",
    ) -> Optional[Dict[str, Any]]:
        data: Dict[str, Any] = {"type": type, "title": title, "source": source}
        if description:
            data["description"] = description
        return await self._post("/api/activity", data)

    # --- Status ---

    async def fetch_status(self) -> Optional[Dict[str, Any]]:
        return await self._get("/api/status")

    # --- Lifecycle ---

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
