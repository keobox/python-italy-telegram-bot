"""Electus bot personality strings - Matrix + Python themed.

All user-facing Italian strings for the bot, themed around Matrix (Neo/Electus)
and Python programming metaphors.
"""

BOT_NAME = "Electus"

# =============================================================================
# WELCOME / CAPTCHA FLOW
# =============================================================================

START_GREETING = (
    "Ciao. Sono Electus, il guardiano della comunità Python Italia.\n"
    "Per completare la verifica in un gruppo, usa il pulsante nel messaggio di benvenuto."
)

VERIFY_READ_RULES_URL = (
    "Per completare la verifica, leggi il regolamento:\n{rules_url}\n\n"
    "Dopo averlo letto, clicca sul link 'Ho letto il CoC' in fondo alla pagina."
)

VERIFY_READ_RULES_CONTENT = (
    "Ecco il regolamento. Leggilo e invia il comando segreto che troverai:\n\n"
    "{content}"
)

VERIFY_SEND_SECRET = "Invia il comando segreto per completare la verifica."

VERIFY_ALREADY_VERIFIED = (
    "Sei già verificato. Puoi partecipare alle discussioni in tutti i gruppi."
)

VERIFY_NO_PENDING = (
    "Non hai gruppi in attesa di verifica. "
    "Se hai appena completato la verifica, potrebbe essere già stata applicata."
)

VERIFY_SUCCESS = (
    "Verifica completata. Accesso liberato—benvenuto nella comunità Python Italia."
)

VERIFY_UNKNOWN_COMMAND = (
    "Comando non riconosciuto. Leggi il regolamento "
    "e invia il comando segreto che troverai."
)

def get_default_welcome_template(bot_username: str) -> str:
    """Return the default welcome message template with Matrix/Python flair."""
    return (
        "Benvenuto {username}. Per accedere alle discussioni, leggi il regolamento.\n"
        f"[Verifica](buttonurl://t.me/{bot_username}?start=verify)"
    )


# =============================================================================
# MODERATION
# =============================================================================

# Common
ONLY_IN_GROUPS = "Questo comando funziona solo nei gruppi."
ONLY_IN_PRIVATE = "Questo comando funziona solo in chat privata."
ONLY_ADMINS = "Solo gli amministratori possono usare questo comando."
USER_NOT_FOUND = "Utente non trovato."

# Force group registration
GROUP_REGISTERED = "Gruppo registrato. Chat ID: {chat_id}"

# Ban
BAN_USAGE = "Uso: /ban user_id [motivo], o rispondi al messaggio con /ban [motivo]."

def ban_success(success_count: int, fail_count: int, reason: str | None) -> str:
    """Format ban success message."""
    msg = f"Utente bannato globalmente in {success_count} gruppi."
    if fail_count > 0:
        msg += f" ({fail_count} falliti)"
    msg += f"\nMotivo: {reason or 'Nessuno'}"
    return msg

# Unban
UNBAN_USAGE = "Uso: /unban user_id, o rispondi al messaggio con /unban"

def unban_success(success_count: int, fail_count: int) -> str:
    """Format unban success message."""
    msg = f"Utente sbannato globalmente da {success_count} gruppi."
    if fail_count > 0:
        msg += f" ({fail_count} falliti)"
    return msg

# Mute
MUTE_USAGE = "Uso: /mute @username [minuti] [motivo], o rispondi al messaggio"

def mute_success(duration: int | None, reason: str | None) -> str:
    """Format mute success message."""
    msg = "Utente mutato"
    if duration:
        msg += f" per {duration} minuti"
    if reason:
        msg += f". Motivo: {reason}"
    return msg

MUTE_FAILED = "Impossibile mutare l'utente."

# Unmute
UNMUTE_USAGE = "Uso: /unmute @username, /unmute user_id, o rispondi al messaggio"
UNMUTE_SUCCESS = "Utente smutato."
UNMUTE_FAILED = "Impossibile smutare l'utente."

# Report
REPORT_USAGE = "Rispondi al messaggio da segnalare con /report [motivo]"
REPORT_SUCCESS = "Segnalazione inviata. Gli amministratori la esamineranno."

# @admin mention
ADMIN_REQUEST_SUCCESS = "Richiesta inviata. Gli amministratori interverranno."


# =============================================================================
# SETTINGS
# =============================================================================

SETWELCOME_USAGE = (
    "Uso: /setwelcome <messaggio>\n\n"
    "Placeholder disponibili:\n"
    "  {username} - @username o nome completo\n"
    "  {chatname} - nome del gruppo\n\n"
    "Sintassi bottoni:\n"
    "  [Testo](buttonurl://URL)"
)
SETWELCOME_SUCCESS = "Messaggio di benvenuto impostato."
RESETWELCOME_SUCCESS = "Messaggio di benvenuto ripristinato al default."
GETWELCOME_CUSTOM = "Messaggio di benvenuto attuale:\n\n{message}"
GETWELCOME_DEFAULT = "Nessun messaggio personalizzato. Default:\n\n{message}"


# =============================================================================
# ID COMMAND
# =============================================================================

ID_RESPONSE = "ID chat: {chat_id}\nID utente: {user_id}"


# =============================================================================
# ANNOUNCE
# =============================================================================

ANNOUNCE_OWNER_ONLY = "Solo il proprietario del bot può usare questo comando."
ANNOUNCE_NO_OWNER_CONFIGURED = "BOT_OWNER_ID non configurato."
ANNOUNCE_USAGE = (
    "Uso: /announce <messaggio>\n\n"
    "Supporta HTML e bottoni: [Testo](buttonurl://url)"
)
ANNOUNCE_EMPTY_MESSAGE = "Il messaggio non può essere vuoto."
ANNOUNCE_NO_GROUPS = "Nessun gruppo registrato."
ANNOUNCE_SENDING = "Invio annuncio a {count} gruppi..."

def announce_result(success: int, failed: int) -> str:
    """Format announcement result message."""
    return f"Annuncio inviato: {success} ok, {failed} falliti."
