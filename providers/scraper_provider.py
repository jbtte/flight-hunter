import os
import re
import requests

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
            timeout=45,
        )
        resp.raise_for_status()
        return _extrair_menor_preco(resp.text)

    except Exception as e:
        print(f"Erro scraper ({origem}-{destino} {data_ida}): {e}")
        return None


def _extrair_menor_preco(html):
    """
    Extrai preços em BRL do HTML renderizado do Google Flights.
    Filtra valores dentro de um range plausível para voos internacionais.
    """
    precos = []

    # Padrão principal: R$ 4.500 ou R$4500
    matches = re.findall(r'R\$\s*([\d\.]+(?:,\d{2})?)', html)
    for m in matches:
        try:
            valor = float(m.replace('.', '').replace(',', '.'))
            if 1000 < valor < 50000:
                precos.append(valor)
        except ValueError:
            pass

    # Padrão alternativo: valor numérico próximo a "BRL" no JSON embutido
    matches_brl = re.findall(r'"BRL[",]\s*"?([\d]+)"?', html)
    for m in matches_brl:
        try:
            valor = float(m)
            if 1000 < valor < 50000:
                precos.append(valor)
        except ValueError:
            pass

    return min(precos) if precos else None
