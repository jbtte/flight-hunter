import asyncio
import logging
from utils.config_loader import CONFIG
from providers.travelpayouts_provider import get_baseline_price, get_calendar_prices, links_compra
from providers.scraper_provider import confirmar_preco_scraper
from providers.social_miner import start_social_monitor
from utils.database import init_db, is_new_pearl, log_scan
from utils.notifier import send_telegram_msg
from datetime import datetime, timedelta, date


def _meses_no_range(start_date_iso, end_date_iso):
    """Retorna lista de strings 'YYYY-MM' cobrindo o range de datas."""
    start = date.fromisoformat(start_date_iso)
    end = date.fromisoformat(end_date_iso)
    meses = []
    atual = date(start.year, start.month, 1)
    while atual <= end:
        meses.append(atual.strftime("%Y-%m"))
        atual = date(atual.year + (atual.month // 12), (atual.month % 12) + 1, 1)
    return meses


def _is_pearl(preco, baseline, threshold, max_price):
    """
    Retorna True se o preço for uma pérola.
    - Com baseline: preço deve estar abaixo de (baseline * (1 - threshold))
    - Sem baseline (Travelpayouts indisponível): usa max_price_threshold como fallback
    """
    if baseline:
        return preco < baseline * (1 - threshold)
    return preco <= max_price


async def rotina_busca_ativa():
    """
    Busca preços via Travelpayouts Calendar (varredura) +
    scrape.do/Google Flights (confirmação apenas quando pérola detectada).
    """
    while True:
        try:
            routes = CONFIG.get("monitored_routes", [])
            settings = CONFIG["search_settings"]
            threshold = settings["pearl_threshold"]
            travel_window = settings["travel_window"]
            loop = asyncio.get_running_loop()
            dur_ref = (travel_window["min_duration_days"] + travel_window["max_duration_days"]) // 2
            meses = _meses_no_range(travel_window["start_date"], travel_window["end_date"])
            start = date.fromisoformat(travel_window["start_date"])
            end = date.fromisoformat(travel_window["end_date"])

            logging.info(f"Iniciando ciclo — calendar {meses}, {len(routes)} rota(s).")

            for route in routes:
                origem = route["origin"]
                destinos = route.get("destinations", [route.get("destination")])
                label = route["label"]
                max_price = route["max_price_threshold"]

                cidade_destino = route.get("city_code", destinos[0])
                baseline = await get_baseline_price(origem, cidade_destino)
                if baseline:
                    logging.info(f"Baseline {label}: R$ {baseline:.2f} | meta: R$ {baseline * (1 - threshold):.2f}")
                else:
                    logging.warning(f"Baseline indisponível para {label}, usando max_price_threshold.")

                melhor_preco = None
                melhor_data_ida = None
                melhor_aeroporto = None

                # Varredura via calendar — 2 chamadas por aeroporto cobre todo o período
                melhor_info = None
                for destino in destinos:
                    calendar = await get_calendar_prices(origem, destino, meses)
                    for date_str, info in calendar.items():
                        data_ida = date.fromisoformat(date_str)
                        if not (start <= data_ida <= end):
                            continue
                        preco = info["price"]
                        logging.info(f"  {origem}→{destino} {date_str}: R$ {preco:.2f} ({info['airline']})")
                        await loop.run_in_executor(
                            None, log_scan, "travelpayouts", label, preco, baseline,
                            _is_pearl(preco, baseline, threshold, max_price), False
                        )
                        if melhor_preco is None or preco < melhor_preco:
                            melhor_preco = preco
                            melhor_data_ida = date_str
                            melhor_aeroporto = destino
                            melhor_info = info

                # Confirmação via scraper apenas se calendar apontou pérola
                if melhor_preco and _is_pearl(melhor_preco, baseline, threshold, max_price):
                    data_volta = (date.fromisoformat(melhor_data_ida) + timedelta(days=dur_ref)).isoformat()
                    logging.info(f"Pérola no calendar! Confirmando via scraper: {melhor_aeroporto} {melhor_data_ida}→{data_volta}")

                    preco_confirmado = await loop.run_in_executor(
                        None, confirmar_preco_scraper, origem, melhor_aeroporto, melhor_data_ida, data_volta
                    )

                    # Sanidade: descarta confirmação se divergir mais de 40% do calendar
                    if preco_confirmado and abs(preco_confirmado - melhor_preco) / melhor_preco < 0.40:
                        preco_final = preco_confirmado
                        fonte = "Google Flights"
                    else:
                        preco_final = melhor_preco
                        fonte = "Travelpayouts" + (" (scraper divergiu)" if preco_confirmado else " (não confirmado)")

                    if await loop.run_in_executor(None, is_new_pearl, "travelpayouts", label, preco_final):
                        data_volta = (date.fromisoformat(melhor_data_ida) + timedelta(days=dur_ref)).isoformat()
                        url_decolar, url_google = links_compra(origem, melhor_aeroporto, melhor_data_ida, data_volta)
                        airline = melhor_info["airline"] if melhor_info else "—"
                        dep = melhor_info.get("departure_at", "")[:16].replace("T", " ") if melhor_info else ""
                        ret = melhor_info.get("return_at", "")[:16].replace("T", " ") if melhor_info else ""

                        msg = (
                            f"💎 <b>[{label}]</b> R$ {preco_final:.2f}\n"
                            f"✈️ {airline} | {melhor_aeroporto}\n"
                            f"📅 Ida: {dep} | Volta: {ret}\n"
                            f"📊 Fonte: {fonte}"
                        )
                        if baseline:
                            msg += f" <i>(baseline: R$ {baseline:.2f})</i>"
                        msg += f"\n\n🛒 <a href='{url_decolar}'>Decolar</a>  🔍 <a href='{url_google}'>Google Flights</a>"
                        await send_telegram_msg(msg)
                        await loop.run_in_executor(
                            None, log_scan, "travelpayouts", label, preco_final, baseline, True, True
                        )


        except Exception as e:
            logging.error(f"Erro no ciclo de busca ativa: {e}")

        await asyncio.sleep(CONFIG["search_settings"]["check_interval_hours"] * 3600)


async def _social_monitor_resiliente():
    """Reinicia o monitor social automaticamente se desconectar."""
    while True:
        try:
            await start_social_monitor()
        except Exception as e:
            logging.error(f"Monitor social desconectou: {e}. Reiniciando em 60s...")
            await asyncio.sleep(60)


async def main():
    init_db()
    print("🚀 Sistema Flight Hunter Pro 2026 Online!")
    await asyncio.gather(_social_monitor_resiliente(), rotina_busca_ativa())


if __name__ == "__main__":
    asyncio.run(main())
