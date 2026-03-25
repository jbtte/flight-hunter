import os
import aiohttp
from datetime import date
from dotenv import load_dotenv

load_dotenv()

TRAVELPAYOUTS_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")


async def get_baseline_price(origem, destino):
    """
    Busca o preço histórico mais barato via Travelpayouts para usar como baseline.
    Retorna o menor preço encontrado em BRL, ou None se não disponível.
    """
    if not TRAVELPAYOUTS_TOKEN:
        return None

    url = "https://api.travelpayouts.com/v1/prices/cheap"
    params = {
        "origin": origem,
        "destination": destino,
        "currency": "brl",
        "token": TRAVELPAYOUTS_TOKEN,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        if not data.get("success"):
            return None

        dest_data = data.get("data", {}).get(destino, {})
        if not dest_data:
            return None

        prices = [entry["price"] for entry in dest_data.values() if "price" in entry]
        return min(prices) if prices else None

    except Exception as e:
        print(f"Erro Travelpayouts baseline ({origem}-{destino}): {e}")
        return None


async def get_calendar_prices(origem, destino, meses):
    """
    Busca preços para cada dia dos meses fornecidos via endpoint de calendário.
    meses: lista de strings 'YYYY-MM'
    Retorna dict {date_iso: price} com todas as datas encontradas.
    """
    if not TRAVELPAYOUTS_TOKEN:
        return {}

    url = "https://api.travelpayouts.com/v1/prices/calendar"
    precos = {}

    async with aiohttp.ClientSession() as session:
        for mes in meses:
            params = {
                "origin": origem,
                "destination": destino,
                "month": mes,
                "currency": "brl",
                "token": TRAVELPAYOUTS_TOKEN,
            }
            try:
                async with session.get(url, params=params) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                if data.get("success"):
                    for date_str, info in data.get("data", {}).items():
                        if isinstance(info, dict) and "price" in info:
                            precos[date_str] = info["price"]
            except Exception as e:
                print(f"Erro Travelpayouts calendar {mes} ({origem}-{destino}): {e}")

    return precos
