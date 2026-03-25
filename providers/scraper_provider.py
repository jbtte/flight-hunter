import os
import re
import requests
from bs4 import BeautifulSoup

SCRAPEDO_TOKEN = os.getenv("SCRAPEDO_TOKEN")


def confirmar_preco_scraper(origem, destino, data_ida, data_volta):
    """
    Confirma preço via scrape.do + Google Flights.
    Usado apenas quando o calendar do Travelpayouts aponta uma pérola.
    Retorna o menor preço encontrado em BRL, ou None em caso de falha.
    """
    if not SCRAPEDO_TOKEN:
        return None

    target_url = (
        f"https://www.google.com/travel/flights"
        f"?hl=pt-BR&curr=BRL"
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
    Extrai preços em BRL do HTML renderizado do Google Flights.
    Tenta múltiplas estratégias já que o Google Flights embute dados em JSON/JS.
    """
    precos = []
    _range_valido = lambda v: 1000 < v < 50000

    # Estratégia 1: R$ X.XXX ou R$X.XXX (formato brasileiro explícito)
    for m in re.findall(r'R\$\s*([\d\.]+(?:,\d{2})?)', html):
        try:
            v = float(m.replace('.', '').replace(',', '.'))
            if _range_valido(v):
                precos.append(v)
        except ValueError:
            pass

    # Estratégia 2: JSON embutido — "BRL","6262" ou ["BRL",6262]
    for m in re.findall(r'["\[]BRL["\],]\s*["\']?(\d{4,5})["\']?', html):
        try:
            v = float(m)
            if _range_valido(v):
                precos.append(v)
        except ValueError:
            pass

    # Estratégia 3: padrão de preço em JSON — "price":6262 ou "totalPrice":6262
    for m in re.findall(r'"(?:price|totalPrice|totalFare|amount)"\s*:\s*(\d{4,5})', html):
        try:
            v = float(m)
            if _range_valido(v):
                precos.append(v)
        except ValueError:
            pass

    # Estratégia 4: aria-label com valor monetário nos elementos da página
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(attrs={"aria-label": True}):
        label = tag["aria-label"]
        for m in re.findall(r'[\d]{1,2}[.,][\d]{3}', label):
            try:
                v = float(m.replace('.', '').replace(',', ''))
                if _range_valido(v):
                    precos.append(v)
            except ValueError:
                pass

    # Estratégia 5: números no formato X.XXX isolados (separador de milhar BRL)
    # Ex: 6.262 → aparece em data-price ou texto de botões
    for m in re.findall(r'\b([4-9]\.\d{3})\b', html):
        try:
            v = float(m.replace('.', ''))
            if _range_valido(v):
                precos.append(v)
        except ValueError:
            pass

    return min(precos) if precos else None
