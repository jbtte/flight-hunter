import os
import re
import requests
from bs4 import BeautifulSoup

SCRAPEDO_TOKEN = os.getenv("SCRAPEDO_TOKEN")


def _get_usd_brl():
    """Busca cotação USD/BRL atual. Retorna fallback 5.5 se falhar."""
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=USD&to=BRL", timeout=5)
        return r.json()["rates"]["BRL"]
    except Exception:
        return 5.5


def confirmar_preco_scraper(origem, destino, data_ida, data_volta):
    """
    Confirma preço via scrape.do + Google Flights.
    Usado apenas quando o calendar do Travelpayouts aponta uma pérola.
    Retorna o menor preço encontrado em BRL, ou None em caso de falha.
    """
    if not SCRAPEDO_TOKEN:
        return None

    # gl=BR + hl=pt-BR + curr=BRL forçam localização brasileira
    target_url = (
        f"https://www.google.com/travel/flights"
        f"?hl=pt-BR&gl=BR&curr=BRL"
        f"&q=flights+from+{origem}+to+{destino}"
        f"+on+{data_ida}+return+{data_volta}"
    )

    try:
        resp = requests.get(
            "https://api.scrape.do",
            params={
                "token": SCRAPEDO_TOKEN,
                "url": target_url,
                "render": "true",
                "geoCode": "br",
            },
            timeout=90,
        )
        resp.raise_for_status()
        return _extrair_menor_preco(resp.text)

    except Exception as e:
        print(f"Erro scraper ({origem}-{destino} {data_ida}): {e}")
        return None


def _extrair_menor_preco(html):
    """
    Extrai preços do HTML renderizado do Google Flights.
    Detecta se os preços estão em BRL ou USD e converte para BRL.
    """
    precos_brl = []
    precos_usd = []
    _range_brl = lambda v: 1000 < v < 50000
    _range_usd = lambda v: 200 < v < 10000

    # Estratégia 1: R$ explícito → BRL
    for m in re.findall(r'R\$\s*([\d\.]+(?:,\d{2})?)', html):
        try:
            v = float(m.replace('.', '').replace(',', '.'))
            if _range_brl(v):
                precos_brl.append(v)
        except ValueError:
            pass

    # Estratégia 2: JSON "BRL" + número → BRL
    for m in re.findall(r'["\[]BRL["\],]\s*["\']?(\d{4,5})["\']?', html):
        try:
            v = float(m)
            if _range_brl(v):
                precos_brl.append(v)
        except ValueError:
            pass

    # Estratégia 3: $ sem R (dólar) → USD
    for m in re.findall(r'(?<!R)\$\s*([\d,]+(?:\.\d{2})?)', html):
        try:
            v = float(m.replace(',', ''))
            if _range_usd(v):
                precos_usd.append(v)
        except ValueError:
            pass

    # Estratégia 4: JSON "USD" + número → USD
    for m in re.findall(r'["\[]USD["\],]\s*["\']?(\d{3,5})["\']?', html):
        try:
            v = float(m)
            if _range_usd(v):
                precos_usd.append(v)
        except ValueError:
            pass

    # Estratégia 5: aria-label com valores monetários
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(attrs={"aria-label": True}):
        label = tag["aria-label"]
        for m in re.findall(r'R\$\s*([\d\.]+)', label):
            try:
                v = float(m.replace('.', ''))
                if _range_brl(v):
                    precos_brl.append(v)
            except ValueError:
                pass

    # Estratégia 6: formato X.XXX isolado (milhar BRL) — ex: 6.262
    for m in re.findall(r'\b([4-9]\.\d{3})\b', html):
        try:
            v = float(m.replace('.', ''))
            if _range_brl(v):
                precos_brl.append(v)
        except ValueError:
            pass

    # Prefere BRL; se só tiver USD, converte
    if precos_brl:
        return min(precos_brl)
    if precos_usd:
        cotacao = _get_usd_brl()
        print(f"  Preços em USD detectados. Convertendo com cotação R$ {cotacao:.2f}/USD.")
        return min(precos_usd) * cotacao
    return None
