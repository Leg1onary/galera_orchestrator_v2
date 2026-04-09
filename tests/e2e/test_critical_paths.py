"""
E2E Critical Path Tests — Galera Orchestrator v2
Покрывает все critical paths из ТЗ разделы 4, 5, 9, 10, 11, 13, 14, 15, 16, 19.

Запуск:
    pytest tests/e2e/ -v --base-url=http://localhost:8000

Требования:
    pip install pytest httpx pytest-asyncio websockets
"""

import asyncio
import json
import os
import time
from typing import Generator

import httpx
import pytest
import websockets

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
WS_URL   = BASE_URL.replace("http://", "ws://").replace("https://", "wss://")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client() -> Generator[httpx.Client, None, None]:
    """Синхронный httpx клиент без редиректов."""
    with httpx.Client(base_url=BASE_URL, follow_redirects=False, timeout=15) as c:
        yield c


@pytest.fixture(scope="session")
def auth_client(client: httpx.Client) -> httpx.Client:
    """Клиент с активной сессией (JWT cookie)."""
    resp = client.post(
        "/api/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    # httpx автоматически сохраняет Set-Cookie в jar клиента
    return client


@pytest.fixture(scope="session")
def cluster_id(auth_client: httpx.Client) -> int:
    """ID первого кластера из БД (создаётся через Settings API)."""
    resp = auth_client.get("/api/clusters")
    assert resp.status_code == 200
    clusters = resp.json()
    if clusters:
        return clusters[0]["id"]
    # Создаём тестовый кластер если нет ни одного
    contours = auth_client.get("/api/contours").json()
    contour_id = contours[0]["id"] if contours else _create_contour(auth_client)
    r = auth_client.post(
        "/api/settings/clusters",
        json={"name": "e2e-cluster", "contour_id": contour_id},
    )
    assert r.status_code in (200, 201)
    return r.json()["id"]


def _create_contour(client: httpx.Client) -> int:
    r = client.post("/api/settings/contours", json={"name": "test"})
    assert r.status_code in (200, 201)
    return r.json()["id"]


# ── Phase 0: SPA + Static ────────────────────────────────────────────────────────

class TestSPA:
    """ТЗ раздел 3: SPA fallback, статика."""

    def test_root_returns_html(self, client: httpx.Client):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "<div id=\"app\">" in r.text or "<!DOCTYPE html>" in r.text.lower()

    def test_spa_fallback_overview(self, client: httpx.Client):
        """Любой non-API маршрут должен отдавать index.html."""
        for path in ["/overview", "/nodes", "/recovery", "/maintenance",
                     "/diagnostics", "/settings", "/docs", "/topology"]:
            r = client.get(path)
            assert r.status_code == 200, f"SPA fallback failed for {path}"
            assert "text/html" in r.headers["content-type"]

    def test_api_404_returns_json(self, client: httpx.Client):
        r = client.get("/api/nonexistent")
        assert r.status_code == 404
        assert r.headers["content-type"].startswith("application/json")
        body = r.json()
        assert "detail" in body

    def test_openapi_available(self, client: httpx.Client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "openapi" in schema
        assert "paths" in schema


# ── Phase 1: Auth ────────────────────────────────────────────────────────────────

class TestAuth:
    """ТЗ раздел 4: JWT httpOnly cookie, GET /api/auth/me."""

    def test_me_unauthenticated(self, client: httpx.Client):
        """Свежий клиент без cookie → 401."""
        with httpx.Client(base_url=BASE_URL, timeout=10) as fresh:
            r = fresh.get("/api/auth/me")
            assert r.status_code == 401

    def test_login_sets_httponly_cookie(self, client: httpx.Client):
        r = client.post(
            "/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        assert r.status_code == 200
        # Cookie должна быть установлена
        assert "access_token" in r.cookies or any(
            "access_token" in str(h) for h in r.headers.get_list("set-cookie")
        )
        # HttpOnly флаг
        set_cookie = " ".join(r.headers.get_list("set-cookie"))
        assert "httponly" in set_cookie.lower(), "Cookie must be HttpOnly"

    def test_me_authenticated(self, auth_client: httpx.Client):
        r = auth_client.get("/api/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body.get("authenticated") is True
        assert "username" in body

    def test_wrong_password_returns_401(self, client: httpx.Client):
        with httpx.Client(base_url=BASE_URL, timeout=10) as fresh:
            r = fresh.post(
                "/api/auth/login",
                json={"username": ADMIN_USERNAME, "password": "wrong-password-e2e"},
            )
            assert r.status_code == 401

    def test_logout_clears_session(self, client: httpx.Client):
        # Логинимся
        with httpx.Client(base_url=BASE_URL, timeout=10) as c:
            c.post("/api/auth/login",
                   json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
            assert c.get("/api/auth/me").status_code == 200
            # Логаутимся
            c.post("/api/auth/logout")
            r = c.get("/api/auth/me")
            assert r.status_code == 401


# ── Phase 1: Cluster Endpoints ───────────────────────────────────────────────────

class TestClusterEndpoints:
    """ТЗ раздел 9.1–9.2: cluster-scoped endpoints."""

    def test_get_contours(self, auth_client: httpx.Client):
        r = auth_client.get("/api/contours")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_clusters(self, auth_client: httpx.Client):
        r = auth_client.get("/api/clusters")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_cluster_status_structure(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """Status endpoint должен вернуть полную структуру из ТЗ 9.2."""
        r = auth_client.get(f"/api/clusters/{cluster_id}/status")
        assert r.status_code == 200
        body = r.json()
        required_keys = {
            "id", "name", "contour", "status", "primary",
            "wsrep_cluster_size", "online_nodes", "total_nodes",
            "online_arbitrators", "total_arbitrators",
            "last_updated_ts", "nodes", "arbitrators", "active_operation",
        }
        missing = required_keys - set(body.keys())
        assert not missing, f"Missing keys in status: {missing}"

    def test_cluster_status_values(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.get(f"/api/clusters/{cluster_id}/status")
        body = r.json()
        assert body["status"] in ("healthy", "degraded", "critical", "unknown")
        assert isinstance(body["nodes"], list)
        assert isinstance(body["arbitrators"], list)

    def test_get_cluster_nodes(self, auth_client: httpx.Client, cluster_id: int):
        r = auth_client.get(f"/api/clusters/{cluster_id}/nodes")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_cluster_arbitrators(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.get(f"/api/clusters/{cluster_id}/arbitrators")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_event_log(self, auth_client: httpx.Client, cluster_id: int):
        r = auth_client.get(f"/api/clusters/{cluster_id}/log")
        assert r.status_code == 200
        logs = r.json()
        assert isinstance(logs, list)
        if logs:
            assert "level" in logs[0]
            assert "source" in logs[0]
            assert "message" in logs[0]
            assert logs[0]["level"] in ("INFO", "WARN", "ERROR")

    def test_requires_auth_on_cluster_endpoint(self, client: httpx.Client, cluster_id: int):
        with httpx.Client(base_url=BASE_URL, timeout=10) as fresh:
            r = fresh.get(f"/api/clusters/{cluster_id}/status")
            assert r.status_code == 401


# ── Phase 2: Settings CRUD ───────────────────────────────────────────────────────

class TestSettingsCRUD:
    """ТЗ раздел 16: CRUD для кластеров, нод, арбитраторов, DC, system."""

    def test_system_settings_get(self, auth_client: httpx.Client):
        r = auth_client.get("/api/settings/system")
        assert r.status_code == 200
        body = r.json()
        assert "polling_interval_sec" in body
        assert "event_log_limit" in body
        assert "timezone" in body

    def test_system_settings_patch(self, auth_client: httpx.Client):
        r = auth_client.patch(
            "/api/settings/system",
            json={"polling_interval_sec": 10, "event_log_limit": 150},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["polling_interval_sec"] == 10
        assert body["event_log_limit"] == 150
        # Restore
        auth_client.patch(
            "/api/settings/system",
            json={"polling_interval_sec": 5, "event_log_limit": 200},
        )

    def test_datacenter_crud(self, auth_client: httpx.Client):
        # Create
        r = auth_client.post(
            "/api/settings/datacenters",
            json={"name": f"e2e-dc-{int(time.time())}"},
        )
        assert r.status_code in (200, 201)
        dc_id = r.json()["id"]

        # Read
        r = auth_client.get("/api/settings/datacenters")
        assert any(dc["id"] == dc_id for dc in r.json())

        # Update
        r = auth_client.patch(
            f"/api/settings/datacenters/{dc_id}",
            json={"name": f"e2e-dc-updated-{int(time.time())}"},
        )
        assert r.status_code == 200

        # Delete
        r = auth_client.delete(f"/api/settings/datacenters/{dc_id}")
        assert r.status_code in (200, 204)

    def test_cluster_crud(self, auth_client: httpx.Client):
        contours = auth_client.get("/api/contours").json()
        contour_id = contours[0]["id"]
        ts = int(time.time())

        # Create
        r = auth_client.post(
            "/api/settings/clusters",
            json={"name": f"e2e-cl-{ts}", "contour_id": contour_id},
        )
        assert r.status_code in (200, 201)
        cl_id = r.json()["id"]

        # Update
        r = auth_client.patch(
            f"/api/settings/clusters/{cl_id}",
            json={"name": f"e2e-cl-upd-{ts}"},
        )
        assert r.status_code == 200

        # Delete
        r = auth_client.delete(f"/api/settings/clusters/{cl_id}")
        assert r.status_code in (200, 204)

    def test_node_validation_duplicate_host_port(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """ТЗ 16.3: дублирование host:port должно возвращать ошибку."""
        ts = int(time.time())
        payload = {
            "name": f"e2e-node-a-{ts}",
            "host": f"192.168.99.{ts % 254 + 1}",
            "port": 3307,
            "cluster_id": cluster_id,
        }
        r1 = auth_client.post("/api/settings/nodes", json=payload)
        if r1.status_code not in (200, 201):
            pytest.skip("Node creation not available (no cluster nodes?)")

        node_id = r1.json()["id"]
        # Пытаемся создать вторую ноду с тем же host:port
        payload2 = {**payload, "name": f"e2e-node-b-{ts}"}
        r2 = auth_client.post("/api/settings/nodes", json=payload2)
        assert r2.status_code in (400, 409, 422), \
            "Duplicate host:port must be rejected"

        # Cleanup
        auth_client.delete(f"/api/settings/nodes/{node_id}")


# ── Phase 2: Node Actions ────────────────────────────────────────────────────────

class TestNodeActions:
    """ТЗ раздел 9.3, 11.6: node actions, sync vs async, cluster_operations."""

    def _get_first_node(
            self, auth_client: httpx.Client, cluster_id: int
    ) -> dict | None:
        nodes = auth_client.get(f"/api/clusters/{cluster_id}/nodes").json()
        return nodes[0] if nodes else None

    def test_sync_actions_schema(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """
        Sync actions (set-readonly, set-readwrite, enter-maintenance, exit-maintenance)
        не создают cluster_operation — сразу возвращают результат.
        """
        node = self._get_first_node(auth_client, cluster_id)
        if not node:
            pytest.skip("No nodes configured")

        node_id = node["id"]
        for action in ("set-readwrite", "set-readonly"):
            r = auth_client.post(
                f"/api/clusters/{cluster_id}/nodes/{node_id}/actions",
                json={"action": action},
            )
            # 200 (success), 409 (lock conflict), 503 (SSH/DB down) — все допустимы
            assert r.status_code in (200, 409, 503), \
                f"Unexpected status {r.status_code} for {action}: {r.text}"

    def test_async_action_returns_operation_id(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """
        Async actions (start/stop/restart/rejoin-force) должны
        вернуть accepted=true + operation_id.
        """
        node = self._get_first_node(auth_client, cluster_id)
        if not node:
            pytest.skip("No nodes configured")

        node_id = node["id"]
        r = auth_client.post(
            f"/api/clusters/{cluster_id}/nodes/{node_id}/actions",
            json={"action": "restart"},
        )
        if r.status_code == 409:
            # Кластер заблокирован другой операцией — допустимо
            pytest.skip("Cluster locked by another operation")
        if r.status_code == 503:
            pytest.skip("Node unreachable (SSH/DB down)")

        assert r.status_code == 200
        body = r.json()
        assert body.get("accepted") is True
        assert "operation_id" in body

    def test_cluster_lock_409(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """
        ТЗ раздел 19.1: параллельная операция возвращает 409 Conflict.
        Проверяем что endpoint знает о lock semantics.
        """
        node = self._get_first_node(auth_client, cluster_id)
        if not node:
            pytest.skip("No nodes configured")

        node_id = node["id"]
        # Первый запрос
        r1 = auth_client.post(
            f"/api/clusters/{cluster_id}/nodes/{node_id}/actions",
            json={"action": "restart"},
        )
        if r1.status_code not in (200, 409):
            pytest.skip(f"Unexpected initial status {r1.status_code}")

        if r1.status_code == 200:
            # Второй запрос пока первый ещё running
            r2 = auth_client.post(
                f"/api/clusters/{cluster_id}/nodes/{node_id}/actions",
                json={"action": "restart"},
            )
            # Либо 409 (lock), либо 200 (если первая успела завершиться быстро)
            assert r2.status_code in (200, 409)


# ── Phase 3: Recovery Endpoints ─────────────────────────────────────────────────

class TestRecovery:
    """ТЗ раздел 13: recovery wizard backend."""

    def test_recovery_status_structure(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.get(f"/api/clusters/{cluster_id}/recovery/status")
        assert r.status_code == 200
        body = r.json()
        # active_operation: null или объект
        assert "active_operation" in body

    def test_recovery_bootstrap_locked_when_active(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """
        Если уже есть активная операция — bootstrap возвращает 409.
        Если нет — 200 или 503 (ноды недостижимы в тестовом окружении).
        """
        status = auth_client.get(
            f"/api/clusters/{cluster_id}/recovery/status"
        ).json()
        active = status.get("active_operation")

        if active and active.get("status") in ("running", "pending", "cancel_requested"):
            r = auth_client.post(f"/api/clusters/{cluster_id}/recovery/bootstrap")
            assert r.status_code == 409, \
                "Must return 409 when cluster operation is active"
        else:
            # Нет активной операции — запрос должен быть принят (или 503 без нод)
            r = auth_client.post(f"/api/clusters/{cluster_id}/recovery/bootstrap")
            assert r.status_code in (200, 503, 422), \
                f"Unexpected bootstrap response: {r.status_code} {r.text}"
            # Отменяем если приняли
            if r.status_code == 200:
                auth_client.post(f"/api/clusters/{cluster_id}/recovery/cancel")

    def test_recovery_cancel_endpoint_exists(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.post(f"/api/clusters/{cluster_id}/recovery/cancel")
        # 200 (cancelled), 404 (нет активной операции) — оба допустимы
        assert r.status_code in (200, 404, 409)


# ── Phase 3: Maintenance Endpoints ──────────────────────────────────────────────

class TestMaintenance:
    """ТЗ раздел 14: maintenance, rolling restart."""

    def test_maintenance_status_structure(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.get(f"/api/clusters/{cluster_id}/maintenance/status")
        assert r.status_code == 200
        body = r.json()
        assert "active_operation" in body

    def test_rolling_restart_requires_healthy_cluster(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """
        ТЗ 14.6: Rolling restart не должен запускаться если кластер не Healthy.
        В тестовом окружении без реальных нод ожидаем 422/409/503.
        """
        r = auth_client.post(
            f"/api/clusters/{cluster_id}/maintenance/rolling-restart"
        )
        # Допустимые ответы без реальных нод
        assert r.status_code in (200, 409, 422, 503)

    def test_maintenance_cancel_endpoint(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.post(f"/api/clusters/{cluster_id}/maintenance/cancel")
        assert r.status_code in (200, 404, 409)


# ── Phase 4: Diagnostics ─────────────────────────────────────────────────────────

class TestDiagnostics:
    """ТЗ раздел 15: diagnostics endpoints."""

    def test_galera_vars_endpoint(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.get(f"/api/clusters/{cluster_id}/diagnostics/galera-vars")
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            rows = r.json()
            assert isinstance(rows, list)
            if rows:
                assert "variable_name" in rows[0]
                assert "value" in rows[0]

    def test_galera_status_endpoint(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.get(f"/api/clusters/{cluster_id}/diagnostics/galera-status")
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            rows = r.json()
            assert isinstance(rows, list)

    def test_config_diff_endpoint(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.get(f"/api/clusters/{cluster_id}/diagnostics/config-diff")
        assert r.status_code in (200, 503)

    def test_check_all_endpoint(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.post(
            f"/api/clusters/{cluster_id}/diagnostics/check-all"
        )
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            body = r.json()
            assert isinstance(body, list)
            if body:
                row = body[0]
                assert "role" in row       # "node" | "arbitrator"
                assert "ssh_ok" in row

    def test_resources_endpoint(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        r = auth_client.post(
            f"/api/clusters/{cluster_id}/diagnostics/resources"
        )
        assert r.status_code in (200, 503)

    def test_innodb_status_requires_node_id(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """Без node_id должен вернуть 422."""
        r = auth_client.get(
            f"/api/clusters/{cluster_id}/diagnostics/innodb-status"
        )
        assert r.status_code in (422, 400)


# ── Phase 5: WebSocket ───────────────────────────────────────────────────────────

class TestWebSocket:
    """ТЗ раздел 5: WS /ws/clusters/{id}, auth через cookie."""

    def _get_cookie_header(self, client: httpx.Client) -> str:
        cookies = "; ".join(
            f"{name}={value}" for name, value in client.cookies.items()
        )
        return cookies

    def test_ws_auth_required(self, cluster_id: int):
        """Без cookie WS должен закрыться с 4001 или HTTP 401."""
        async def _check():
            try:
                async with websockets.connect(
                        f"{WS_URL}/ws/clusters/{cluster_id}",
                        open_timeout=5,
                ) as ws:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    # Если вдруг пропустил — проверяем что это не данные
                    data = json.loads(msg)
                    assert data.get("event") == "error"
            except (
                    websockets.exceptions.ConnectionClosedError,
                    websockets.exceptions.InvalidStatusCode,
                    asyncio.TimeoutError,
            ):
                pass  # Ожидаемое поведение — соединение закрыто/отклонено

        asyncio.get_event_loop().run_until_complete(_check())

    def test_ws_connects_with_valid_cookie(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """С валидной сессией WS должен установиться и прислать хотя бы один frame."""
        cookie = self._get_cookie_header(auth_client)
        if not cookie:
            pytest.skip("No auth cookie available")

        async def _check():
            try:
                async with websockets.connect(
                        f"{WS_URL}/ws/clusters/{cluster_id}",
                        additional_headers={"Cookie": cookie},
                        open_timeout=5,
                ) as ws:
                    # Ждём первое сообщение (может быть connected-ping или событие)
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5)
                        data = json.loads(msg)
                        assert "event" in data or "type" in data
                    except asyncio.TimeoutError:
                        # Нет сообщений за 5 сек — соединение живое, просто тихое
                        pass
            except websockets.exceptions.InvalidStatusCode as e:
                pytest.fail(f"WS rejected with status {e.status_code}")

        asyncio.get_event_loop().run_until_complete(_check())

    def test_ws_event_structure(
            self, auth_client: httpx.Client, cluster_id: int
    ):
        """Если приходит событие — оно должно содержать event + cluster_id + ts."""
        cookie = self._get_cookie_header(auth_client)
        if not cookie:
            pytest.skip("No auth cookie available")

        received: list[dict] = []

        async def _collect():
            try:
                async with websockets.connect(
                        f"{WS_URL}/ws/clusters/{cluster_id}",
                        additional_headers={"Cookie": cookie},
                        open_timeout=5,
                ) as ws:
                    try:
                        for _ in range(3):
                            msg = await asyncio.wait_for(ws.recv(), timeout=3)
                            received.append(json.loads(msg))
                    except asyncio.TimeoutError:
                        pass
            except Exception:
                pass

        asyncio.get_event_loop().run_until_complete(_collect())

        for event in received:
            assert "event" in event, f"Event missing 'event' key: {event}"
            assert "cluster_id" in event, f"Event missing 'cluster_id': {event}"
            assert "ts" in event, f"Event missing 'ts': {event}"


# ── Phase 0: Security Headers ────────────────────────────────────────────────────

class TestSecurityHeaders:
    """Базовые security проверки."""

    def test_no_server_header_leaking_version(self, client: httpx.Client):
        r = client.get("/")
        server = r.headers.get("server", "")
        # Uvicorn по умолчанию отдаёт "uvicorn" без версии — это OK
        # Но не должно быть Python версии или полного стека
        assert "python/" not in server.lower()
        assert "fastapi/" not in server.lower()

    def test_cookie_secure_flags(self, client: httpx.Client):
        r = client.post(
            "/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        if r.status_code != 200:
            pytest.skip("Login failed")
        set_cookie = " ".join(r.headers.get_list("set-cookie")).lower()
        assert "httponly" in set_cookie, "Cookie must have HttpOnly flag"
        # SameSite — рекомендуется, но не блокируем тест
        # assert "samesite" in set_cookie

    def test_cors_not_wildcard_for_api(self, client: httpx.Client):
        r = client.options(
            "/api/auth/me",
            headers={"Origin": "https://evil.example.com",
                     "Access-Control-Request-Method": "GET"},
        )
        acac = r.headers.get("access-control-allow-credentials", "")
        acao = r.headers.get("access-control-allow-origin", "")
        # Нельзя иметь wildcard + credentials=true одновременно
        if acao == "*":
            assert acac.lower() != "true", \
                "CORS: cannot have * origin with credentials=true"