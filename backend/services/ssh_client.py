"""
SSHClient — paramiko-based SSH client for node management.

Per ТЗ раздел 15.11:
  - SSH connect timeout: 5s
  - SSH command execute timeout: 10s

Usage as context manager:
    with SSHClient(host, port, user) as ssh:
        stdout, stderr = ssh.execute("hostname")

Usage standalone:
    ssh = SSHClient(host, port, user)
    try:
        ssh.connect()
        result = ssh.execute("hostname")
    finally:
        ssh.close()
"""

import logging
import time
from typing import Self
import socket

import shlex

import paramiko

from config import settings

logger = logging.getLogger(__name__)

# Per ТЗ раздел 15.11
SSH_CONNECT_TIMEOUT_SEC = 5
SSH_EXECUTE_TIMEOUT_SEC = 10


class SSHError(Exception):
    """Raised when an SSH operation fails."""


class SSHClient:
    """
    Thin wrapper around paramiko.SSHClient.

    Per ТЗ раздел 3.2: one global SSH key, mounted read-only at
    settings.SSH_KEY_PATH. No per-node key configuration.
    """

    def __init__(
            self,
            host: str,
            port: int = 22,
            username: str = "root",
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self._client: paramiko.SSHClient | None = None

    # ── Connection lifecycle ──────────────────────────────────────────────────

    def connect(self) -> None:
        """
        Open SSH connection using the global key from settings.SSH_KEY_PATH.

        Raises:
            SSHError: if the connection cannot be established within 5 seconds,
                      or if authentication fails.
        """
        client = paramiko.SSHClient()
        # AutoAddPolicy: trust all host keys automatically.
        # Per ТЗ this is acceptable — all managed hosts are known infrastructure.
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                key_filename=str(settings.SSH_KEY_PATH),
                timeout=SSH_CONNECT_TIMEOUT_SEC,
                # Disable password auth — key-only per ТЗ раздел 3.2
                allow_agent=False,
                look_for_keys=False,
            )
        except paramiko.AuthenticationException as exc:
            raise SSHError(
                f"SSH auth failed for {self.username}@{self.host}:{self.port} — "
                f"check SSH_KEY_PATH ({settings.SSH_KEY_PATH}): {exc}"
            ) from exc
        except paramiko.SSHException as exc:
            raise SSHError(
                f"SSH error connecting to {self.host}:{self.port}: {exc}"
            ) from exc
        except OSError as exc:
            # Covers ConnectionRefusedError, TimeoutError, etc.
            raise SSHError(
                f"Cannot reach {self.host}:{self.port} — {exc}"
            ) from exc

        self._client = client
        logger.debug("SSH connected to %s:%s as %s", self.host, self.port, self.username)

    def close(self) -> None:
        """Close the SSH connection if open."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            finally:
                self._client = None
                logger.debug("SSH disconnected from %s:%s", self.host, self.port)

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
        # Do not suppress exceptions
        return None

    # ── Command execution ─────────────────────────────────────────────────────

    def execute(self, command: str, check: bool = False) -> tuple[str, str]:
        """
        Execute a command over SSH.

        Args:
            command: shell command to run on the remote host.
            check:   if True, raise SSHError when the remote exit code is
                     non-zero.  Use this for destructive/management commands
                     (systemctl start/stop/restart) where a non-zero exit
                     code means the action genuinely failed.
                     Defaults to False for backward-compatibility with
                     read-only queries that may return non-zero (e.g. grep).

        Returns:
            (stdout, stderr) as stripped UTF-8 strings.

        Raises:
            SSHError: on connection/transport errors, timeout, or (when
                      check=True) non-zero remote exit code.
        """
        if self._client is None:
            raise SSHError("Not connected — call connect() first")

        try:
            _, stdout, stderr = self._client.exec_command(
                command,
                timeout=SSH_EXECUTE_TIMEOUT_SEC,
            )
            # Устанавливаем channel timeout чтобы stdout.read() не блокировал вечно
            stdout.channel.settimeout(SSH_EXECUTE_TIMEOUT_SEC)
            stderr.channel.settimeout(SSH_EXECUTE_TIMEOUT_SEC)

            out = stdout.read().decode("utf-8", errors="replace").strip()
            err = stderr.read().decode("utf-8", errors="replace").strip()
            exit_code = stdout.channel.recv_exit_status()
        except (TimeoutError, socket.timeout) as exc:
            raise SSHError(
                f"SSH exec timed out [{self.host}:{self.port}] `{command}`"
            ) from exc
        except paramiko.SSHException as exc:
            raise SSHError(
                f"SSH exec failed [{self.host}:{self.port}] `{command}`: {exc}"
            ) from exc
        except OSError as exc:
            raise SSHError(
                f"SSH exec I/O error [{self.host}:{self.port}] `{command}`: {exc}"
            ) from exc

        logger.debug(
            "SSH exec [%s:%s] `%s` → exit=%d stdout=%r stderr=%r",
            self.host, self.port, command, exit_code, out[:200], err[:200],
        )

        if check and exit_code != 0:
            detail = err or out or "(no output)"
            raise SSHError(
                f"Command failed (exit {exit_code}) [{self.host}:{self.port}] "
                f"`{command}`: {detail}"
            )

        return out, err

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def test_connection(self) -> float:
        """
        Verify connectivity by executing `echo ok` and measuring round-trip latency.

        Returns:
            latency_ms: float — round-trip time in milliseconds

        Raises:
            SSHError: if connection or execution fails
        """
        if self._client is None:
            self.connect()

        t0 = time.monotonic()
        out, _ = self.execute("echo ok")
        latency_ms = (time.monotonic() - t0) * 1000

        if out != "ok":
            raise SSHError(
                f"Unexpected response from {self.host}:{self.port} — "
                f"expected 'ok', got {out!r}"
            )

        logger.debug(
            "SSH test_connection %s:%s OK — %.1f ms", self.host, self.port, latency_ms
        )
        return round(latency_ms, 2)

    def read_file(self, path: str) -> str:
        out, err = self.execute(f"cat {shlex.quote(path)}")
        if err and not out:
            raise SSHError(f"Cannot read {path} on {self.host}: {err}")
        return out

    def check_process_running(self, process_name: str) -> bool:
        try:
            out, _ = self.execute(f"pgrep -x {shlex.quote(process_name)} | head -1")
            return bool(out.strip())
        except SSHError:
            return False
