import asyncio
import logging
from utils.config_loader import CONFIG
from providers.duffel_provider import buscar_passagem_dinamica
from providers.travelpayouts_provider import get_baseline_price
from providers.social_miner import start_social_monitor
from utils.database import init_db, is_new_pearl
from utils.notifier import send_telegram_msg
from datetime import datetime, timedelta


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
    """Percorre as rotas do config.json e busca preços"""
    while True:
        try:
            routes = CONFIG.get("monitored_routes", [])
            settings = CONFIG["search_settings"]
            days_ahead = settings["days_ahead"]
            duration = settings["default_duration_days"]
            threshold = settings["pearl_threshold"]

            ida = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            volta = (datetime.now() + timedelta(days=days_ahead + duration)).strftime("%Y-%m-%d")

            loop = asyncio.get_running_loop()

            for route in routes:
                origem, destino = route["origin"], route["destination"]
                label = route["label"]
                max_price = route["max_price_threshold"]

                # Baseline de preço via Travelpayouts
                baseline = await get_baseline_price(origem, destino)
                if baseline:
                    logging.info(f"Baseline {label}: R$ {baseline:.2f} | meta: R$ {baseline * (1 - threshold):.2f}")
                else:
                    logging.warning(f"Baseline indisponível para {label}, usando max_price_threshold como fallback.")

                # 1. Duffel
                res_duffel = await loop.run_in_executor(
                    None, buscar_passagem_dinamica, origem, destino, ida, volta
                )
                if res_duffel and _is_pearl(res_duffel["preco"], baseline, threshold, max_price):
                    if await loop.run_in_executor(None, is_new_pearl, "duffel", label, res_duffel["preco"]):
                        await send_telegram_msg(
                            f"💎 **Duffel [{label}]:** R$ {res_duffel['preco']:.2f}\n"
                            f"_(baseline: R$ {baseline:.2f})_" if baseline else
                            f"💎 **Duffel [{label}]:** R$ {res_duffel['preco']:.2f}"
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
