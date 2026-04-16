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

from database import engine, _migrate_system_settings, _migrate_arbitrators, _migrate_backup_servers
from sqlalchemy import text
import models  # ensure metadata is populated for create_all

def run() -> None:
    # create_all creates backup_servers and any other new tables idempotently
    models.metadata.create_all(engine)
    with engine.begin() as conn:
        _migrate_system_settings(conn)
        _migrate_arbitrators(conn)
        _migrate_backup_servers(conn)
    print("Migration complete.")

if __name__ == "__main__":
    run()
