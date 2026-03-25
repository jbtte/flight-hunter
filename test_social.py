"""
Script de teste para o Social Mining.
Roda fora do main.py para validar cada parte isoladamente.

Testes:
  1. Conexão com Telegram e acesso aos canais monitorados
  2. Lógica de keywords (simula mensagens sem acessar canais reais)
  3. Notificador (envia mensagem real no seu Telegram)

Uso:
  source venv/bin/activate
  python3 test_social.py
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from utils.config_loader import CONFIG
from utils.database import init_db, log_social_hit

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
CHANNELS = ["passagensimperdiveis", "melhoresdestinos"]


# ─── Teste 1: Conexão e acesso aos canais ────────────────────────────────────

async def teste_conexao():
    print("\n[1] Testando conexão com Telegram e acesso aos canais...")
    client = TelegramClient("session_hunter", API_ID, API_HASH)
    await client.start()

    ok = []
    falhou = []
    for canal in CHANNELS:
        try:
            entity = await client.get_entity(canal)
            print(f"  ✓ {canal} — {entity.title}")
            ok.append(canal)
        except Exception as e:
            print(f"  ✗ {canal} — ERRO: {e}")
            falhou.append(canal)

    await client.disconnect()
    print(f"\n  Resultado: {len(ok)}/{len(CHANNELS)} canais acessíveis.")
    if falhou:
        print(f"  Canais com problema: {falhou}")
    return len(falhou) == 0


# ─── Teste 2: Lógica de keywords (sem Telegram) ───────────────────────────────

def teste_keywords():
    print("\n[2] Testando lógica de keywords...")
    keywords = CONFIG.get("social_keywords", [])
    priority_keywords = CONFIG.get("priority_keywords", [])

    mensagens_teste = [
        ("Passagem GRU para Tokyo por R$ 3200!", True, False),
        ("Erro tarifário urgente: Brasil para Japão!", True, True),
        ("Promoção para Paris saindo de Lisboa", False, False),
        ("Narita com tarifas históricas essa semana", True, True),
        ("Voo Osaka ida e volta bem barato", True, False),
    ]

    todos_ok = True
    for msg, esperado_match, esperado_priority in mensagens_teste:
        msg_lower = msg.lower()
        match = any(k in msg_lower for k in keywords)
        priority = any(k in msg_lower for k in priority_keywords)

        status_match = "✓" if match == esperado_match else "✗"
        status_priority = "✓" if priority == esperado_priority else "✗"

        print(f"  {status_match} match={match} {status_priority} priority={priority} | \"{msg[:50]}\"")

        if match != esperado_match or priority != esperado_priority:
            todos_ok = False

    print(f"\n  Keywords carregadas: {keywords}")
    print(f"  Priority keywords: {priority_keywords}")
    return todos_ok


# ─── Teste 3: Notificador ─────────────────────────────────────────────────────

async def teste_notificador():
    print("\n[3] Testando envio de notificação pelo Telegram Bot...")
    from utils.notifier import send_telegram_msg
    try:
        await send_telegram_msg(
            "🧪 <b>Teste do Flight Hunter Pro</b>\n\n"
            "Social Mining conectado e funcionando.\n"
            "Canais monitorados: passagensimperdiveis, melhoresdestinos"
        )
        print("  ✓ Mensagem enviada — verifique seu Telegram.")
        return True
    except Exception as e:
        print(f"  ✗ Falha ao enviar: {e}")
        return False


# ─── Teste 4: Banco de dados ──────────────────────────────────────────────────

def teste_banco():
    print("\n[4] Testando escrita no banco de dados...")
    try:
        init_db()
        log_social_hit(
            channel="teste",
            message="Mensagem de teste do script test_social.py",
            is_priority=False,
            was_notified=False,
        )
        print("  ✓ Registro salvo em data/flights.db (tabela social_hits).")
        return True
    except Exception as e:
        print(f"  ✗ Erro no banco: {e}")
        return False


# ─── Runner ───────────────────────────────────────────────────────────────────

async def main():
    print("=" * 55)
    print("  Flight Hunter Pro — Teste do Social Mining")
    print("=" * 55)

    resultados = {}
    resultados["conexao"] = await teste_conexao()
    resultados["keywords"] = teste_keywords()
    resultados["banco"] = teste_banco()
    resultados["notificador"] = await teste_notificador()

    print("\n" + "=" * 55)
    print("  Resumo:")
    for nome, ok in resultados.items():
        print(f"  {'✓' if ok else '✗'} {nome}")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
