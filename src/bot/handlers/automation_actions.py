"""Automation action wizards triggered from the /menu InlineKeyboard."""

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = structlog.get_logger()


async def automation_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle auto:* callbacks — start automation wizards."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "auto:instagram_carousel":
        text = (
            "📸 <b>Instagram Carousel Generator</b>\n\n"
            "Reply to this message with a <b>topic</b> and I'll generate a carousel for you.\n\n"
            "<i>Example: \"5 tips for better sleep\"</i>"
        )
        context.user_data["pending_automation"] = "instagram_carousel"

    elif data == "auto:blog_post":
        text = (
            "📝 <b>Blog Post Generator</b>\n\n"
            "Reply to this message with a <b>topic</b> and I'll draft a blog post.\n\n"
            "<i>Example: \"How AI is transforming healthcare\"</i>"
        )
        context.user_data["pending_automation"] = "blog_post"

    elif data == "auto:social_post":
        text = (
            "📣 <b>Social Post Generator</b>\n\n"
            "Reply to this message with a <b>topic</b> and I'll create social media posts.\n\n"
            "<i>Example: \"Launch of our new feature\"</i>"
        )
        context.user_data["pending_automation"] = "social_post"

    else:
        return

    cancel_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="menu:automations")]
    ])

    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=cancel_kb)
    except Exception as e:
        logger.debug("Failed to edit automation message", error=str(e))


async def handle_automation_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Check if a pending automation is active and process the input.

    Returns True if the message was consumed by an automation wizard,
    False if it should be passed through to normal message handling.
    """
    pending = context.user_data.get("pending_automation")
    if not pending:
        return False

    # Clear the pending flag
    context.user_data.pop("pending_automation", None)
    topic = update.message.text

    # Send processing indicator
    progress_msg = await update.message.reply_text(
        f"⏳ Processing <b>{pending.replace('_', ' ').title()}</b>...\n\n"
        f"Topic: <i>{topic[:100]}</i>",
        parse_mode="HTML",
    )

    # Try to run via AutomationEngine
    engine = context.bot_data.get("automation_engine")
    bridge = context.bot_data.get("bridge")

    # Track execution in bridge
    execution_id = None
    if bridge:
        try:
            result = await bridge.start_automation(
                name=pending,
                type=pending,
                triggered_by=f"telegram:{update.effective_user.id}",
                input_data={"topic": topic},
            )
            if result:
                execution_id = result.get("executionId")
        except Exception as e:
            logger.debug("Bridge automation start failed", error=str(e))

    try:
        if engine:
            method = getattr(engine, pending, None)
            if method:
                result_text = await method(topic)
            else:
                result_text = f"Automation '{pending}' is not yet implemented."
        else:
            result_text = (
                f"🚧 <b>{pending.replace('_', ' ').title()}</b> automation is being set up.\n\n"
                f"Topic: <i>{topic[:200]}</i>\n\n"
                f"<i>The AutomationEngine will handle this once configured.</i>"
            )

        await progress_msg.edit_text(result_text, parse_mode="HTML")

        # Mark complete in bridge
        if bridge and execution_id:
            bridge.fire_and_forget(
                bridge.complete_automation(execution_id, {"output": result_text[:500]})
            )

    except Exception as e:
        logger.error("Automation failed", automation=pending, error=str(e))
        await progress_msg.edit_text(
            f"❌ <b>Automation Failed</b>\n\n{str(e)[:300]}",
            parse_mode="HTML",
        )
        if bridge and execution_id:
            bridge.fire_and_forget(
                bridge.fail_automation(execution_id, str(e)[:300])
            )

    return True
