#!/usr/bin/env python
"""
Standalone migration script.
Запускать вручную при обновлении схемы на уже существующей БД:

    python migrate.py

Эквивалентно вызову init_db() но без пересева данных.
Безопасно для повторного запуска.
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from database import engine, _migrate_system_settings
from sqlalchemy import text

def run() -> None:
    with engine.begin() as conn:
        _migrate_system_settings(conn)
    print("Migration complete.")

if __name__ == "__main__":
    run()
