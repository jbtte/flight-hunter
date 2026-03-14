import sqlite3
from datetime import datetime

DB_PATH = "data/flights.db"


def init_db():
    """Cria as tabelas se não existirem. Execute isso no início do main.py"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            route TEXT,
            price REAL,
            date_info TEXT,
            timestamp DATETIME
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            route TEXT,
            price_found REAL,
            baseline REAL,
            was_pearl INTEGER DEFAULT 0,
            was_notified INTEGER DEFAULT 0,
            timestamp DATETIME
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS social_hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            message TEXT,
            is_priority INTEGER DEFAULT 0,
            was_notified INTEGER DEFAULT 0,
            timestamp DATETIME
        )
    """
    )
    conn.commit()
    conn.close()


def log_scan(provider, route, price_found, baseline, was_pearl, was_notified):
    """Registra cada execução de scan, independente de ser pérola."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO scans (provider, route, price_found, baseline, was_pearl, was_notified, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (provider, route, price_found, baseline, int(was_pearl), int(was_notified), datetime.now()),
    )
    conn.commit()
    conn.close()


def log_social_hit(channel, message, is_priority, was_notified):
    """Registra cada mensagem de canal que bateu em alguma keyword."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO social_hits (channel, message, is_priority, was_notified, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """,
        (channel, message, int(is_priority), int(was_notified), datetime.now()),
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
