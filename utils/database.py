import sqlite3
from datetime import datetime

DB_PATH = "data/flights.db"


def init_db():
    """Cria a tabela se ela não existir. Execute isso no início do main.py"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,      -- 'duffel', 'social', 'scraper'
            route TEXT,         -- 'GRU-MIA'
            price REAL,         -- 2500.00
            date_info TEXT,     -- 'Outubro/2026' ou '12 dias'
            timestamp DATETIME
        )
    """
    )
    conn.commit()
    conn.close()


def is_new_pearl(provider, route, price):
    """
    Verifica se o preço atual é menor que o último registrado para essa rota.
    Retorna True se for uma promoção nova/melhor.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Busca o último preço salvo para este provedor e rota
    cursor.execute(
        """
        SELECT price FROM history 
        WHERE provider = ? AND route = ? 
        ORDER BY timestamp DESC LIMIT 1
    """,
        (provider, route),
    )

    row = cursor.fetchone()

    # Se nunca viu essa rota ou se o preço atual for 5% menor que o anterior
    # (Usamos uma margem de 5% para evitar notificações por oscilações centavos)
    is_new = row is None or price < (row[0] * 0.95)

    try:
        if is_new:
            cursor.execute(
                """
                INSERT INTO history (provider, route, price, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (provider, route, price, datetime.now()),
            )
            conn.commit()
    finally:
        conn.close()

    return is_new
