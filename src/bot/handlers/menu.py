"""Smart /menu system with InlineKeyboard navigation."""

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = structlog.get_logger()

# --- Menu Layouts ---

def _main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Automations", callback_data="menu:automations"),
            InlineKeyboardButton("📊 Monitoring", callback_data="menu:monitoring"),
        ],
        [
            InlineKeyboardButton("📁 Projects", callback_data="menu:projects"),
            InlineKeyboardButton("⚡ Quick Actions", callback_data="menu:quick"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings"),
        ],
    ])


def _automations_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📸 Instagram Carousel", callback_data="auto:instagram_carousel"),
        ],
        [
            InlineKeyboardButton("📝 Blog Post", callback_data="auto:blog_post"),
        ],
        [
            InlineKeyboardButton("📣 Social Post", callback_data="auto:social_post"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="menu:main"),
        ],
    ])


def _monitoring_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💓 System Status", callback_data="mon:status"),
        ],
        [
            InlineKeyboardButton("📈 Recent Activity", callback_data="mon:activity"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="menu:main"),
        ],
    ])


def _projects_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 List Projects", callback_data="proj:list"),
        ],
        [
            InlineKeyboardButton("🔄 Sync Threads", callback_data="proj:sync"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="menu:main"),
        ],
    ])


def _quick_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🆕 New Session", callback_data="quick:new"),
            InlineKeyboardButton("📊 Status", callback_data="quick:status"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="menu:main"),
        ],
    ])


def _settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔊 Verbose Level", callback_data="set:verbose"),
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="menu:main"),
        ],
    ])


# --- Command Handler ---

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu command — show main menu."""
    await update.message.reply_text(
        "📋 <b>Agentik Monitor</b>\n\nChoose a section:",
        parse_mode="HTML",
        reply_markup=_main_menu_keyboard(),
    )


# --- Callback Router ---

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all menu:* callback queries by editing the current message."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu:main":
        text = "📋 <b>Agentik Monitor</b>\n\nChoose a section:"
        keyboard = _main_menu_keyboard()

    elif data == "menu:automations":
        text = "🤖 <b>Automations</b>\n\nSelect an automation to run:"
        keyboard = _automations_keyboard()

    elif data == "menu:monitoring":
        text = "📊 <b>Monitoring</b>\n\nSelect a monitoring action:"
        keyboard = _monitoring_keyboard()

    elif data == "menu:projects":
        text = "📁 <b>Projects</b>\n\nManage your projects:"
        keyboard = _projects_keyboard()

    elif data == "menu:quick":
        text = "⚡ <b>Quick Actions</b>\n\nSelect an action:"
        keyboard = _quick_actions_keyboard()

    elif data == "menu:settings":
        text = "⚙️ <b>Settings</b>\n\nConfigure the bot:"
        keyboard = _settings_keyboard()

    else:
        return

    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        logger.debug("Failed to edit menu message", error=str(e))


# --- Monitoring Callbacks ---

async def monitoring_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle mon:* callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "mon:status":
        bridge = context.bot_data.get("bridge")
        if bridge:
            status = await bridge.fetch_status()
            if status:
                text = (
                    "💓 <b>System Status</b>\n\n"
                    f"<pre>{_format_status(status)}</pre>"
                )
            else:
                text = "💓 <b>System Status</b>\n\n⚠️ Could not fetch status from dashboard."
        else:
            text = "💓 <b>System Status</b>\n\n⚠️ Bridge not configured."

        back_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="menu:monitoring")]
        ])
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_kb)
        except Exception as e:
            logger.debug("Failed to edit monitoring message", error=str(e))

    elif data == "mon:activity":
        text = "📈 <b>Recent Activity</b>\n\n<i>Check the dashboard for full activity feed.</i>"
        back_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="menu:monitoring")]
        ])
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_kb)
        except Exception as e:
            logger.debug("Failed to edit activity message", error=str(e))


# --- Quick Action Callbacks ---

async def quick_action_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle quick:* callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "quick:new":
        context.user_data["force_new_session"] = True
        context.user_data.pop("claude_session_id", None)
        text = "🆕 <b>New Session</b>\n\nSession reset. Send your next message to start fresh."
    elif data == "quick:status":
        session_id = context.user_data.get("claude_session_id", "None")
        text = f"📊 <b>Session Status</b>\n\nSession ID: <code>{session_id}</code>"
    else:
        return

    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:quick")]
    ])
    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_kb)
    except Exception as e:
        logger.debug("Failed to edit quick action message", error=str(e))


# --- Project Callbacks ---

async def project_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle proj:* callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "proj:list":
        settings = context.bot_data.get("settings")
        if settings:
            text = f"📋 <b>Projects Directory</b>\n\n<code>{settings.approved_directory}</code>"
        else:
            text = "📋 <b>Projects</b>\n\n<i>Settings not available.</i>"
    elif data == "proj:sync":
        text = "🔄 <b>Sync Threads</b>\n\nUse /sync_threads command to sync project topics."
    else:
        return

    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:projects")]
    ])
    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_kb)
    except Exception as e:
        logger.debug("Failed to edit project message", error=str(e))


# --- Settings Callbacks ---

async def settings_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle set:* callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "set:verbose":
        current = context.user_data.get("verbose_level", 1)
        new_level = (current + 1) % 3
        context.user_data["verbose_level"] = new_level
        labels = {0: "Quiet", 1: "Normal", 2: "Detailed"}
        text = f"🔊 <b>Verbose Level</b>\n\nChanged to: <b>{labels[new_level]}</b> ({new_level})"
    else:
        return

    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:settings")]
    ])
    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_kb)
    except Exception as e:
        logger.debug("Failed to edit settings message", error=str(e))


def _format_status(status: dict) -> str:
    """Format status dict into readable text."""
    lines = []
    for key, value in status.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines) if lines else "No status data"
