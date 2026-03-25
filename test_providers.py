"""
Script de teste para os providers de preço.
Valida Travelpayouts (baseline + calendar) e scrape.do (Google Flights).

Uso:
  source venv/bin/activate
  python3 test_providers.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


# ─── Teste 1: Travelpayouts Baseline ─────────────────────────────────────────

async def teste_travelpayouts_baseline():
    print("\n[1] Testando Travelpayouts — baseline price...")
    from providers.travelpayouts_provider import get_baseline_price

    baseline = await get_baseline_price("GRU", "TYO")
    if baseline:
        print(f"  ✓ GRU→NRT baseline: R$ {baseline:.2f}")
        return True
    else:
        print("  ✗ Sem resposta — token inválido ou rota sem dados históricos.")
        return False


# ─── Teste 2: Travelpayouts Calendar ─────────────────────────────────────────

async def teste_travelpayouts_calendar():
    print("\n[2] Testando Travelpayouts — calendar prices (out/nov 2026)...")
    from providers.travelpayouts_provider import get_calendar_prices

    resultados = {}
    for destino in ["NRT", "HND"]:
        precos = await get_calendar_prices("GRU", destino, ["2026-10", "2026-11"])
        resultados[destino] = precos
        if precos:
            menor = min(precos.values())
            melhor_data = min(precos, key=precos.get)
            print(f"  ✓ GRU→{destino}: {len(precos)} datas encontradas | menor: R$ {menor:.2f} em {melhor_data}")
        else:
            print(f"  ✗ GRU→{destino}: sem dados retornados.")

    # Mostra as 5 datas mais baratas entre os dois aeroportos
    todos = {}
    for destino, precos in resultados.items():
        for data, preco in precos.items():
            todos[f"{destino} {data}"] = preco

    if todos:
        print("\n  Top 5 datas mais baratas:")
        for chave, preco in sorted(todos.items(), key=lambda x: x[1])[:5]:
            print(f"    R$ {preco:.2f} — {chave}")

    return any(resultados.values())


# ─── Teste 3: scrape.do + Google Flights ─────────────────────────────────────

def teste_scraper():
    print("\n[3] Testando scrape.do — confirmação de preço via Google Flights...")
    from providers.scraper_provider import confirmar_preco_scraper

    token = os.getenv("SCRAPEDO_TOKEN")
    if not token:
        print("  ✗ SCRAPEDO_TOKEN não encontrado no .env")
        return False

    # Usa uma data próxima ao período de interesse
    preco = confirmar_preco_scraper("GRU", "NRT", "2026-10-08", "2026-10-23")

    if preco:
        print(f"  ✓ Preço confirmado via Google Flights: R$ {preco:.2f}")
        return True
    else:
        print("  ✗ Nenhum preço extraído — HTML retornado abaixo para diagnóstico.")
        _debug_scraper("GRU", "NRT", "2026-10-08", "2026-10-23")
        return False


def _debug_scraper(origem, destino, data_ida, data_volta):
    """Mostra trechos do HTML retornado pelo scrape.do para ajudar a ajustar o parser."""
    import requests, re
    token = os.getenv("SCRAPEDO_TOKEN")
    target_url = (
        f"https://www.google.com/travel/flights"
        f"?hl=pt-BR&curr=BRL"
        f"&q=flights+from+{origem}+to+{destino}"
        f"+on+{data_ida}+return+{data_volta}"
    )
    try:
        resp = requests.get(
            "https://api.scrape.do",
            params={"token": token, "url": target_url, "render": "true", "geoCode": "br"},
            timeout=90,
        )
        html = resp.text
        print(f"\n  Status scrape.do: {resp.status_code} | HTML: {len(html)} chars")

        padroes = {
            "R$ explícito":   r'.{20}R\$.{20}',
            "BRL + número":   r'.{10}BRL.{0,5}\d{4,5}.{10}',
            '"price":NNNNN':  r'.{5}"(?:price|totalPrice|amount)"\s*:\s*\d{4,5}.{5}',
            "X.XXX isolado":  r'\b[4-9]\.\d{3}\b',
        }
        encontrou = False
        for nome, pat in padroes.items():
            matches = re.findall(pat, html)
            if matches:
                print(f"\n  [{nome}] — {len(matches)} ocorrências:")
                for m in matches[:3]:
                    print(f"    {m.strip()}")
                encontrou = True

        if not encontrou:
            print("  Nenhum padrão de preço encontrado.")
            print(f"  Primeiros 300 chars:\n  {html[:300]}")
    except Exception as e:
        print(f"  Erro ao chamar scrape.do: {e}")


# ─── Runner ───────────────────────────────────────────────────────────────────

async def main():
    print("=" * 55)
    print("  Flight Hunter Pro — Teste dos Providers")
    print("=" * 55)

    resultados = {}
    resultados["travelpayouts_baseline"] = await teste_travelpayouts_baseline()
    resultados["travelpayouts_calendar"] = await teste_travelpayouts_calendar()
    resultados["scraper_scrape.do"] = teste_scraper()

    print("\n" + "=" * 55)
    print("  Resumo:")
    for nome, ok in resultados.items():
        print(f"  {'✓' if ok else '✗'} {nome}")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
