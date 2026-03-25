import os
import aiohttp
import logging
from dotenv import load_dotenv

load_dotenv()

# Configurações do Telegram vindas do .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


async def send_telegram_msg(message):
    """
    Envia uma mensagem formatada para o seu Telegram.
    Usa Parse Mode Markdown para mensagens bonitas.
    """
    if not TOKEN or not CHAT_ID:
        logging.error("Configurações do Telegram ausentes no .env")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                response.raise_for_status()
        logging.info(f"Notificação enviada com sucesso: {message[:30]}...")
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para o Telegram: {e}")
