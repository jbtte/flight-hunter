import os
import aiohttp
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
