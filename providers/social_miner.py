import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from utils.config_loader import CONFIG
from utils.notifier import send_telegram_msg
from utils.database import log_social_hit

load_dotenv()

# Credenciais continuam vindo do .env por segurança
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
CHANNELS = ["passagensimperdiveis", "melhoresdestinos"]

client = TelegramClient("session_hunter", API_ID, API_HASH)


@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    msg_original = event.message.message
    msg_lower = msg_original.lower()

    # Puxa as keywords dinamicamente do JSON
    keywords = CONFIG.get("social_keywords", [])

    if any(key in msg_lower for key in keywords):
        priority_keywords = CONFIG.get("priority_keywords", [])
        is_priority = any(x in msg_lower for x in priority_keywords)

        prefixo = (
            "🚨 <b>PÉROLA PRIORITÁRIA</b>" if is_priority else "🎯 <b>Interesse Detectado</b>"
        )

        await send_telegram_msg(
            f"{prefixo}\n\n"
            f"Fonte: {event.chat.title}\n"
            f"Mensagem: {msg_original[:200]}..."
        )
        log_social_hit(event.chat.title, msg_original[:500], is_priority, was_notified=True)


async def start_social_monitor():
    await client.start()
    await client.run_until_disconnected()
