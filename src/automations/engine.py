"""AutomationEngine — orchestrates content generation automations."""

import logging
from typing import Any, Dict, Optional

from .composio_client import ComposioClient

logger = logging.getLogger(__name__)


class AutomationEngine:
    """Engine that runs content generation automations.

    Each method corresponds to an automation type from the /menu system.
    Currently returns placeholder content; will be wired to Claude + Composio.
    """

    def __init__(
        self,
        claude_integration: Any = None,
        composio_client: Optional[ComposioClient] = None,
        bridge: Any = None,
    ) -> None:
        self._claude = claude_integration
        self._composio = composio_client or ComposioClient()
        self._bridge = bridge

    async def instagram_carousel(self, topic: str) -> str:
        """Generate an Instagram carousel from a topic.

        Args:
            topic: The subject of the carousel.

        Returns:
            Formatted HTML string with carousel slides.
        """
        logger.info("Generating Instagram carousel", topic=topic[:80])

        if self._claude:
            try:
                response = await self._claude.run_command(
                    prompt=(
                        f"Generate an Instagram carousel with 5-7 slides about: {topic}\n"
                        "Format each slide as:\n"
                        "Slide N: [Title]\n[Content - 2-3 sentences]\n\n"
                        "Make it engaging, use emojis, and include a CTA on the last slide."
                    ),
                    working_directory="/tmp",
                    user_id=0,
                )
                content = response.content
            except Exception as e:
                logger.warning("Claude carousel generation failed", error=str(e))
                content = self._placeholder_carousel(topic)
        else:
            content = self._placeholder_carousel(topic)

        # Publish via Composio (stub)
        if self._composio and self._composio.enabled:
            await self._composio.execute_action(
                "instagram", "create_carousel", {"content": content, "topic": topic}
            )

        return (
            f"📸 <b>Instagram Carousel</b>\n"
            f"Topic: <i>{_escape(topic[:100])}</i>\n\n"
            f"{content}"
        )

    async def blog_post(self, topic: str) -> str:
        """Generate a blog post draft from a topic.

        Args:
            topic: The subject of the blog post.

        Returns:
            Formatted HTML string with blog post content.
        """
        logger.info("Generating blog post", topic=topic[:80])

        if self._claude:
            try:
                response = await self._claude.run_command(
                    prompt=(
                        f"Write a short blog post outline (500 words max) about: {topic}\n"
                        "Include: Title, Introduction, 3-4 sections with headers, Conclusion.\n"
                        "Use a professional but engaging tone."
                    ),
                    working_directory="/tmp",
                    user_id=0,
                )
                content = response.content
            except Exception as e:
                logger.warning("Claude blog generation failed", error=str(e))
                content = self._placeholder_blog(topic)
        else:
            content = self._placeholder_blog(topic)

        return (
            f"📝 <b>Blog Post Draft</b>\n"
            f"Topic: <i>{_escape(topic[:100])}</i>\n\n"
            f"{content}"
        )

    async def social_post(self, topic: str) -> str:
        """Generate social media posts from a topic.

        Args:
            topic: The subject of the social posts.

        Returns:
            Formatted HTML string with social post variants.
        """
        logger.info("Generating social posts", topic=topic[:80])

        if self._claude:
            try:
                response = await self._claude.run_command(
                    prompt=(
                        f"Generate 3 social media posts about: {topic}\n"
                        "For each platform:\n"
                        "1. Twitter/X (280 chars, with hashtags)\n"
                        "2. LinkedIn (professional tone, 150 words)\n"
                        "3. Instagram caption (engaging, with emojis and hashtags)\n"
                    ),
                    working_directory="/tmp",
                    user_id=0,
                )
                content = response.content
            except Exception as e:
                logger.warning("Claude social generation failed", error=str(e))
                content = self._placeholder_social(topic)
        else:
            content = self._placeholder_social(topic)

        return (
            f"📣 <b>Social Posts</b>\n"
            f"Topic: <i>{_escape(topic[:100])}</i>\n\n"
            f"{content}"
        )

    # --- Placeholders (when Claude is not available) ---

    @staticmethod
    def _placeholder_carousel(topic: str) -> str:
        return (
            f"<b>Slide 1:</b> Introduction to {_escape(topic[:60])}\n"
            f"<b>Slide 2:</b> Key insight #1\n"
            f"<b>Slide 3:</b> Key insight #2\n"
            f"<b>Slide 4:</b> Key insight #3\n"
            f"<b>Slide 5:</b> Call to action\n\n"
            f"<i>🚧 Connect Claude to generate real content.</i>"
        )

    @staticmethod
    def _placeholder_blog(topic: str) -> str:
        return (
            f"<b>Title:</b> Everything About {_escape(topic[:60])}\n\n"
            f"<b>Introduction</b>\n[Introduction paragraph]\n\n"
            f"<b>Section 1</b>\n[Content]\n\n"
            f"<b>Section 2</b>\n[Content]\n\n"
            f"<b>Conclusion</b>\n[Wrap up]\n\n"
            f"<i>🚧 Connect Claude to generate real content.</i>"
        )

    @staticmethod
    def _placeholder_social(topic: str) -> str:
        return (
            f"<b>Twitter/X:</b>\n"
            f"[Tweet about {_escape(topic[:40])}] #topic\n\n"
            f"<b>LinkedIn:</b>\n"
            f"[Professional post about {_escape(topic[:40])}]\n\n"
            f"<b>Instagram:</b>\n"
            f"[Caption about {_escape(topic[:40])}] 📸✨\n\n"
            f"<i>🚧 Connect Claude to generate real content.</i>"
        )


def _escape(text: str) -> str:
    """Simple HTML escape for user-provided text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
