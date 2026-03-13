import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from utils.config_loader import CONFIG
from utils.notifier import send_telegram_msg

load_dotenv()

# Credenciais continuam vindo do .env por segurança
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
CHANNELS = ["passagensimperdiveis", "melhoresdestinos", "secretflying", "flyous"]

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
            "🚨 **PÉROLA PRIORITÁRIA**" if is_priority else "🎯 **Interesse Detectado**"
        )

        await send_telegram_msg(
            f"{prefixo}\n\n"
            f"Fonte: {event.chat.title}\n"
            f"Mensagem: {msg_original[:200]}..."
        )


async def start_social_monitor():
    await client.start()
    await client.run_until_disconnected()
