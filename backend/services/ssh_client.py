from __future__ import annotations

from config import settings


class SSHClient:
    """
    SSH client wrapper around paramiko for executing commands on nodes
    and arbitrators.

    STUB — Phase 1 implementation.

    Responsibilities (to implement in Phase 1):
    - Connect using the global SSH key at settings.SSH_KEY_PATH
    - execute(command) → stdout, stderr, exit_code
    - test_connection() → latency_ms or raise
    - Context manager support (__enter__ / __exit__)

    Timeouts (per ТЗ section 15.11):
    - SSH connect timeout: 5 seconds
    - Diagnostic SSH commands: 10 seconds
    """

    def __init__(self, host: str, port: int = 22, username: str = "root") -> None:
        self.host = host
        self.port = port
        self.username = username
        self.key_path = settings.SSH_KEY_PATH
        self._client = None

    def connect(self) -> None:
        """Establish SSH connection. Implement in Phase 1."""
        raise NotImplementedError("SSHClient.connect() not implemented — Phase 1")

    def execute(self, command: str, timeout: int = 10) -> tuple[str, str, int]:
        """
        Execute a command over SSH.

        Returns:
            (stdout, stderr, exit_code)

        Implement in Phase 1.
        """
        raise NotImplementedError("SSHClient.execute() not implemented — Phase 1")

    def test_connection(self) -> float:
        """
        Test SSH connectivity and return latency in milliseconds.
        Raises on failure. Implement in Phase 1.
        """
        raise NotImplementedError(
            "SSHClient.test_connection() not implemented — Phase 1"
        )

    def close(self) -> None:
        """Close the SSH connection. Implement in Phase 1."""
        raise NotImplementedError("SSHClient.close() not implemented — Phase 1")

    def __enter__(self) -> "SSHClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()