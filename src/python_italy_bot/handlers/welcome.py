"""Welcome and captcha handlers for new members."""

import logging

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..services.captcha import CaptchaService

logger = logging.getLogger(__name__)


def create_welcome_handlers(captcha_service: CaptchaService) -> list:
    """Create welcome and captcha handlers."""
    return [
        ChatMemberHandler(
            _handle_new_member,
            ChatMemberHandler.CHAT_MEMBER,
        ),
        CommandHandler("start", _handle_start),
        MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
            _handle_private_message,
        ),
    ]


async def _handle_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle new chat members: restrict and send welcome with captcha instructions."""
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    result = update.chat_member
    if result is None:
        return

    new_status = result.new_chat_member.status
    old_status = result.old_chat_member.status if result.old_chat_member else None

    if new_status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED):
        return
    if old_status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):
        return

    user = result.new_chat_member.user
    chat = update.effective_chat
    if user is None or chat is None:
        return

    if user.is_bot:
        return

    if await captcha_service.is_globally_verified(user.id):
        return

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            permissions=captcha_service.get_restricted_permissions(),
        )
    except Exception as e:
        logger.warning("Could not restrict user %s in chat %s: %s", user.id, chat.id, e)
        return

    await captcha_service.add_pending(user.id, chat.id)

    bot_me = await context.bot.get_me()
    bot_username = bot_me.username or "bot"

    custom_template = await captcha_service.get_welcome_message(chat.id)
    if custom_template:
        template = custom_template
    else:
        template = captcha_service.get_default_welcome_template(bot_username)

    formatted = captcha_service.format_welcome_message(template, user, chat, bot_username)
    text, keyboard = captcha_service.parse_button_urls(formatted)

    try:
        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.warning("Could not send welcome to chat %s: %s", chat.id, e)


async def _handle_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /start command, including deep link for verification."""
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    message = update.message
    if message is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type != "private":
        return

    user = update.effective_user
    if user is None:
        return

    args = context.args
    if args and args[0] == "verify":
        rules_url = captcha_service.get_rules_url()
        if rules_url:
            await message.reply_text(
                f"Per completare la verifica, leggi il regolamento:\n{rules_url}\n\n"
                "Dopo averlo letto, clicca sul link 'Ho letto il CoC' in fondo alla pagina."
            )
        else:
            captcha_content = captcha_service.get_captcha_file_content()
            if captcha_content:
                await message.reply_text(
                    "Ecco il regolamento. Leggilo e invia il comando segreto che troverai:\n\n"
                    f"{captcha_content[:4000]}"
                )
            else:
                await message.reply_text(
                    "Invia il comando segreto per completare la verifica."
                )
    elif args and args[0] == "CoCDoneLink":
        await _verify_user(user, captcha_service, context, message)
    else:
        await message.reply_text(
            "Ciao! Sono il bot di Python Italia.\n"
            "Se devi completare la verifica per un gruppo, usa il pulsante nel messaggio di benvenuto."
        )


async def _verify_user(
    user,
    captcha_service: CaptchaService,
    context: ContextTypes.DEFAULT_TYPE,
    message,
) -> None:
    """Verify a user globally and unrestrict in all pending groups."""
    if await captcha_service.is_globally_verified(user.id):
        await message.reply_text(
            "Sei già verificato! Puoi partecipare alle discussioni in tutti i gruppi."
        )
        return

    pending_chats = await captcha_service.get_pending_chats(user.id)
    if not pending_chats:
        await message.reply_text(
            "Non hai gruppi in attesa di verifica. "
            "Se hai appena completato la verifica, potrebbe essere già stata applicata."
        )
        return

    await captcha_service.verify_user_globally(user.id)

    for chat_id in pending_chats:
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user.id,
                permissions=captcha_service.get_full_permissions(),
            )
        except Exception as e:
            logger.warning(
                "Could not unrestrict user %s in chat %s: %s", user.id, chat_id, e
            )

    await message.reply_text(
        "Verifica completata! Ora puoi partecipare alle discussioni "
        "in tutti i gruppi Python Italia."
    )


async def _handle_private_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle private messages: check for secret command and verify user globally."""
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    message = update.message
    if message is None or message.text is None:
        return

    user = update.effective_user
    if user is None:
        return

    if not captcha_service.is_secret_command(message.text):
        await message.reply_text(
            "Comando non riconosciuto. Leggi il regolamento "
            "e invia il comando segreto che troverai."
        )
        return

    await _verify_user(user, captcha_service, context, message)
