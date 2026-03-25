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


def links_compra(origem, destino, data_ida, data_volta):
    """Gera links de busca no Decolar e Google Flights para as datas informadas."""
    decolar = (
        f"https://www.decolar.com/passagens-aereas/resultado"
        f"/{origem}/{destino}/{data_ida}/{data_volta}/1/0/0/NA/NA/NA"
    )
    google = (
        f"https://www.google.com/travel/flights?hl=pt-BR&gl=BR&curr=BRL"
        f"&q=voos+de+{origem}+para+{destino}+em+{data_ida}+volta+{data_volta}"
    )
    return decolar, google


AIRLINES = {
    "LA": "LATAM", "JJ": "LATAM", "NH": "ANA", "JL": "JAL",
    "AA": "American Airlines", "UA": "United Airlines", "CX": "Cathay Pacific",
    "KE": "Korean Air", "OZ": "Asiana", "TK": "Turkish Airlines",
    "EK": "Emirates", "QR": "Qatar Airways", "SQ": "Singapore Airlines",
    "MH": "Malaysia Airlines", "BR": "EVA Air", "CI": "China Airlines",
    "CA": "Air China", "MU": "China Eastern",
}


async def get_calendar_prices(origem, destino, meses):
    """
    Busca preços para cada dia dos meses fornecidos via endpoint de calendário.
    meses: lista de strings 'YYYY-MM'
    Retorna dict {date_iso: {price, airline, airline_code, departure_at, return_at}}
    """
    if not TRAVELPAYOUTS_TOKEN:
        return {}

    url = "https://api.travelpayouts.com/v1/prices/calendar"
    resultado = {}

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
                            code = info.get("airline", "")
                            resultado[date_str] = {
                                "price": info["price"],
                                "airline_code": code,
                                "airline": AIRLINES.get(code, code),
                                "departure_at": info.get("departure_at", ""),
                                "return_at": info.get("return_at", ""),
                            }
            except Exception as e:
                print(f"Erro Travelpayouts calendar {mes} ({origem}-{destino}): {e}")

    return resultado
