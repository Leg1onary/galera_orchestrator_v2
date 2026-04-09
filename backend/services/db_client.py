from __future__ import annotations

from services.crypto import decrypt_password


class DBClient:
    """
    MariaDB client wrapper around pymysql for querying Galera nodes.

    STUB — Phase 1 implementation.

    Responsibilities (to implement in Phase 1):
    - Connect to MariaDB using stored credentials (db_user, db_password)
    - db_password is stored encrypted; use decrypt_password() before use
    - query(sql) → list[dict]
    - test_connection() → latency_ms or raise
    - Context manager support

    Timeouts (per ТЗ section 15.11):
    - DB connect timeout: 3 seconds
    """

    def __init__(
            self,
            host: str,
            port: int = 3306,
            user: str | None = None,
            encrypted_password: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        # Decrypt password only when needed (lazy)
        self._encrypted_password = encrypted_password
        self._connection = None

    @property
    def password(self) -> str | None:
        """Return decrypted password on demand."""
        if self._encrypted_password is None:
            return None
        return decrypt_password(self._encrypted_password)

    def connect(self) -> None:
        """Establish MariaDB connection. Implement in Phase 1."""
        raise NotImplementedError("DBClient.connect() not implemented — Phase 1")

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        """
        Execute a SQL query and return results as list of dicts.
        Implement in Phase 1.
        """
        raise NotImplementedError("DBClient.query() not implemented — Phase 1")

    def test_connection(self) -> float:
        """
        Test DB connectivity and return latency in milliseconds.
        Raises on failure. Implement in Phase 1.
        """
        raise NotImplementedError(
            "DBClient.test_connection() not implemented — Phase 1"
        )

    def close(self) -> None:
        """Close the database connection. Implement in Phase 1."""
        raise NotImplementedError("DBClient.close() not implemented — Phase 1")

    def __enter__(self) -> "DBClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()