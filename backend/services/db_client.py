"""
DBClient — pymysql-based MariaDB client for node status queries.

Per ТЗ раздел 15.11:
  - DB connect timeout: 3s
  - DB query timeout (read_timeout): 10s

Node db_password is stored Fernet-encrypted in SQLite.
DBClient decrypts on instantiation via _decrypt_password().

Usage as context manager:
    with DBClient(host, port, user, encrypted_password) as db:
        rows = db.query("SHOW GLOBAL STATUS LIKE 'wsrep%'")

Usage standalone:
    db = DBClient(host, port, user, encrypted_password)
    try:
        db.connect()
        rows = db.query("SELECT 1")
    finally:
        db.close()
"""

import logging
import time
from typing import Any, Self

import pymysql
import pymysql.cursors
from cryptography.fernet import Fernet, InvalidToken

from config import settings

logger = logging.getLogger(__name__)

# Per ТЗ раздел 15.11
DB_CONNECT_TIMEOUT_SEC = 3
DB_READ_TIMEOUT_SEC = 10


class DBError(Exception):
    """Raised when a database operation fails."""


class DBClient:
    """
    Thin wrapper around pymysql for executing status queries on Galera nodes.

    Per ТЗ раздел 2.4: db_password is stored Fernet-encrypted.
    Per ТЗ раздел 3.3: FERNET_SECRET_KEY is loaded from settings.
    """

    def __init__(
            self,
            host: str,
            port: int = 3306,
            user: str = "root",
            encrypted_password: str = "",
            database: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.database = database
        # Decrypt password at construction time — fail fast if key is wrong
        self._password = self._decrypt_password(encrypted_password)
        self._conn: pymysql.connections.Connection | None = None

    # ── Password handling ─────────────────────────────────────────────────────

    @staticmethod
    def _decrypt_password(raw: str) -> str:
        """
        Attempt Fernet decryption of the stored password.

        Falls back to returning the raw string if:
          - The value is empty (node has no DB password configured)
          - Decryption fails (value is plain-text, e.g. in dev environment)

        This dual-mode behaviour allows dev environments to store plain-text
        passwords in .env.dev without requiring Fernet encryption.
        """
        if not raw:
            return ""

        try:
            fernet = Fernet(settings.FERNET_SECRET_KEY.encode())
            return fernet.decrypt(raw.encode()).decode()
        except (InvalidToken, Exception):
            # Not a Fernet token — treat as plain-text (dev mode)
            logger.debug(
                "db_password is not a Fernet token — using as plain-text (dev mode)"
            )
            return raw

    @staticmethod
    def encrypt_password(plain: str) -> str:
        """
        Encrypt a plain-text password for storage in SQLite.
        Used by Settings CRUD when saving node db_password.

        Args:
            plain: plain-text password

        Returns:
            Fernet-encrypted token string
        """
        fernet = Fernet(settings.FERNET_SECRET_KEY.encode())
        return fernet.encrypt(plain.encode()).decode()

    # ── Connection lifecycle ──────────────────────────────────────────────────

    def connect(self) -> None:
        """
        Open a pymysql connection.

        Raises:
            DBError: if the connection cannot be established within 3 seconds.
        """
        try:
            self._conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self._password,
                database=self.database or None,
                connect_timeout=DB_CONNECT_TIMEOUT_SEC,
                read_timeout=DB_READ_TIMEOUT_SEC,
                write_timeout=DB_READ_TIMEOUT_SEC,
                cursorclass=pymysql.cursors.DictCursor,
                # Autocommit for read-only status queries
                autocommit=True,
            )
        except pymysql.OperationalError as exc:
            raise DBError(
                f"Cannot connect to MariaDB at {self.host}:{self.port} "
                f"as {self.user}: {exc}"
            ) from exc
        except Exception as exc:
            raise DBError(
                f"Unexpected DB error connecting to {self.host}:{self.port}: {exc}"
            ) from exc

        logger.debug(
            "DB connected to %s:%s as %s", self.host, self.port, self.user
        )

    def close(self) -> None:
        """Close the DB connection if open."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None
                logger.debug("DB disconnected from %s:%s", self.host, self.port)

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
        return None

    # ── Query execution ───────────────────────────────────────────────────────

    def query(self, sql: str, args: tuple | dict | None = None) -> list[dict[str, Any]]:
        """
        Execute a SQL statement and return all rows as a list of dicts.

        Args:
            sql:  SQL statement string
            args: optional query parameters (passed to cursor.execute)

        Returns:
            list of row dicts (empty list if no rows)

        Raises:
            DBError: if not connected, or if query execution fails
        """
        if self._conn is None:
            raise DBError("Not connected — call connect() first")

        try:
            with self._conn.cursor() as cursor:
                cursor.execute(sql, args)
                return cursor.fetchall()
        except pymysql.Error as exc:
            raise DBError(
                f"Query failed on {self.host}:{self.port}: {exc}\nSQL: {sql}"
            ) from exc
        except Exception as exc:
            raise DBError(
                f"Unexpected error querying {self.host}:{self.port}: {exc}"
            ) from exc

    def query_one(self, sql: str, args: tuple | dict | None = None) -> dict[str, Any] | None:
        """
        Execute a SQL statement and return a single row, or None.

        Args:
            sql:  SQL statement string
            args: optional query parameters

        Returns:
            single row dict or None if no rows
        """
        rows = self.query(sql, args)
        return rows[0] if rows else None

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def test_connection(self) -> float:
        """
        Verify connectivity by executing SELECT 1 and measuring latency.

        Returns:
            latency_ms: float — round-trip time in milliseconds

        Raises:
            DBError: if connection or query fails
        """
        if self._conn is None:
            self.connect()

        t0 = time.monotonic()
        row = self.query_one("SELECT 1 AS ok")
        latency_ms = (time.monotonic() - t0) * 1000

        if not row or row.get("ok") != 1:
            raise DBError(
                f"Unexpected SELECT 1 result from {self.host}:{self.port}: {row}"
            )

        logger.debug(
            "DB test_connection %s:%s OK — %.1f ms", self.host, self.port, latency_ms
        )
        return round(latency_ms, 2)

    def execute(self, sql: str) -> None:
        """Execute a non-SELECT statement (SET GLOBAL, etc.)."""
        if self._conn is None:
            raise DBError("Not connected — call connect() first")

        try:
            with self._conn.cursor() as cursor:
                cursor.execute(sql)
            self._conn.commit()
        except pymysql.Error as exc:
            raise DBError(
                f"Execute failed on {self.host}:{self.port}: {exc}\nSQL: {sql}"
            ) from exc
        except Exception as exc:
            raise DBError(
                f"Unexpected error executing on {self.host}:{self.port}: {exc}"
            ) from exc
