"""
Nodes router — Phase 2

Cluster-scoped per ТЗ. All routes under /api/clusters/{cluster_id}/...

Sync actions (immediate, no lock needed):
  set-readonly | set-readwrite | enter-maintenance | exit-maintenance

Async actions (cluster_operations, lock required):
  start | stop | restart | rejoin-force

GET  /api/clusters/{cluster_id}/nodes                          — список нод кластера
GET  /api/clusters/{cluster_id}/nodes/sst-status              — (вне MVP) SST stuck detection  ← MUST be before /{node_id}
GET  /api/clusters/{cluster_id}/nodes/{node_id}               — конфиг + live state
PATCH /api/clusters/{cluster_id}/nodes/{node_id}              — enable/disable
GET  /api/clusters/{cluster_id}/nodes/{node_id}/test-connection
GET  /api/clusters/{cluster_id}/nodes/{node_id}/innodb-status
POST /api/clusters/{cluster_id}/nodes/{node_id}/actions
POST /api/clusters/{cluster_id}/nodes/{node_id}/rejoin
POST /api/clusters/{cluster_id}/nodes/{node_id}/desync
POST /api/clusters/{cluster_id}/nodes/{node_id}/resync
POST /api/clusters/{cluster_id}/nodes/{node_id}/purge-binary-logs
POST /api/clusters/{cluster_id}/nodes/{node_id}/flush         — (вне MVP) FLUSH LOGS / FTWRL / UNLOCK
POST /api/clusters/{cluster_id}/nodes/{node_id}/restart-sst   — (вне MVP) restart stuck SST

GET  /api/clusters/{cluster_id}/operations/active
POST /api/clusters/{cluster_id}/operations/cancel
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import text

from database import engine
from dependencies import require_auth
from services.db_client import DBClient, DBError
from services.event_log import write_event
from services.operations import (
    assert_no_active_operation,
    create_operation,
    get_active_operation,
    is_cancel_requested,
    request_cancel,
    set_operation_status,
)
from services.poller import live_node_states, poll_single_node, SST_STUCK_THRESHOLD_SEC, SST_STUCK_STATES
from services.ssh_client import SSHClient, SSHError
from services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/clusters",
    tags=["nodes"],
    dependencies=[Depends(require_auth)],
)

# ── Constants ───────────────────────────────────────────────────────

SYNC_ACTIONS  = frozenset({"set-readonly", "set-readwrite", "enter-maintenance", "exit-maintenance"})
ASYNC_ACTIONS = frozenset({"start", "stop", "restart", "rejoin-force"})
ALL_ACTIONS   = SYNC_ACTIONS | ASYNC_ACTIONS

SSH_CONNECT_TIMEOUT = 5
DB_CONNECT_TIMEOUT  = 3

FLUSH_OPERATIONS = frozenset({"logs", "tables_read_lock", "unlock_tables"})

FLUSH_SQL_MAP = {
    "logs":              "FLUSH LOGS",
    "tables_read_lock":  "FLUSH TABLES WITH READ LOCK",
    "unlock_tables":     "UNLOCK TABLES",
}

# ── Schemas ────────────────────────────────────────────────────────

class NodeActionRequest(BaseModel):
    action: str

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ALL_ACTIONS:
            raise ValueError(
                f"Unknown action '{v}'. Valid: {sorted(ALL_ACTIONS)}"
            )
        return v


class NodePatchRequest(BaseModel):
    enabled:     bool | None = None
    maintenance: bool | None = None


class PurgeBinaryLogsRequest(BaseModel):
    mode: str  # 'date' | 'days' — informational only, before_date is always provided
    before_date: str  # 'YYYY-MM-DD HH:MM:SS'

    @field_validator("before_date")
    @classmethod
    def validate_before_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("before_date must be in format 'YYYY-MM-DD HH:MM:SS'")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ("date", "days"):
            raise ValueError("mode must be 'date' or 'days'")
        return v


class FlushRequest(BaseModel):
    operation: str  # 'logs' | 'tables_read_lock' | 'unlock_tables'

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        if v not in FLUSH_OPERATIONS:
            raise ValueError(
                f"Unknown flush operation '{v}'. Valid: {sorted(FLUSH_OPERATIONS)}"
            )
        return v


# ── DB helpers ───────────────────────────────────────────────────────────

def _fetch_node(cluster_id: int, node_id: int) -> dict:
    """Load node row. Raises 404 if not found or belongs to different cluster."""
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                 SELECT n.*, d.name AS datacenter_name
                 FROM nodes n
                          LEFT JOIN datacenters d ON d.id = n.datacenter_id
                 WHERE n.id = :nid AND n.cluster_id = :cid
                 """),
            {"nid": node_id, "cid": cluster_id},
        ).mappings().fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found in cluster {cluster_id}",
        )
    return dict(row)


def _assert_cluster_exists(cluster_id: int) -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM clusters WHERE id = :cid"),
            {"cid": cluster_id},
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster {cluster_id} not found",
        )


# ── GET /api/clusters/{cluster_id}/nodes ────────────────────────────────────────────────────────

@router.get("/{cluster_id}/nodes")
async def list_nodes(cluster_id: int) -> list[dict]:
    _assert_cluster_exists(cluster_id)
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                 SELECT n.*, d.name AS datacenter_name
                 FROM nodes n
                          LEFT JOIN datacenters d ON d.id = n.datacenter_id
                 WHERE n.cluster_id = :cid
                 ORDER BY n.name
                 """),
            {"cid": cluster_id},
        ).mappings().fetchall()

    result = []
    for n in rows:
        node = dict(n)
        live = live_node_states.get(cluster_id, {}).get(node["id"])
        result.append({
            "id":             node["id"],
            "name":           node["name"],
            "host":           node["host"],
            "port":           node["port"],
            "ssh_port":       node["ssh_port"],
            "ssh_user":       node["ssh_user"],
            "db_user":        node["db_user"],
            "enabled":        bool(node["enabled"]),
            "maintenance":    bool(node["maintenance"]),
            "datacenter_id":  node["datacenter_id"],
            "datacenter_name": node["datacenter_name"],
            "cluster_id":     node["cluster_id"],
            "live":           live.to_dict() if live is not None else None,
        })
    return result


# ── GET /api/clusters/{cluster_id}/nodes/sst-status (вне MVP) ──────────────────────────
# ВАЖНО: этот роут зарегистрирован ДО /{node_id}, иначе FastAPI
# трактует строку "sst-status" как int node_id и возвращает 422.

@router.get("/{cluster_id}/nodes/sst-status")
async def get_sst_status(cluster_id: int) -> list[dict]:
    """
    (вне MVP) SST Stuck Detector.
    Возвращает список нод в SST_STUCK_STATES,
    указывая сколько секунд они застряли и превышают ли порог.
    """
    _assert_cluster_exists(cluster_id)
    now = datetime.now(timezone.utc)
    cluster_states = live_node_states.get(cluster_id, {})

    result = []
    for node_id, live in cluster_states.items():
        if not live.wsrep_local_state_comment:
            continue
        state_upper = live.wsrep_local_state_comment.upper()
        if state_upper not in SST_STUCK_STATES:
            continue

        stuck_for_sec: float | None = None
        is_stuck = False

        if live.state_since_ts is not None:
            since = live.state_since_ts
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            stuck_for_sec = (now - since).total_seconds()
            is_stuck = stuck_for_sec >= SST_STUCK_THRESHOLD_SEC

        result.append({
            "node_id":        node_id,
            "state":          live.wsrep_local_state_comment,
            "state_since_ts": live.state_since_ts.isoformat() if live.state_since_ts else None,
            "stuck_for_sec":  round(stuck_for_sec, 1) if stuck_for_sec is not None else None,
            "is_stuck":       is_stuck,
        })

    return result


# ── GET /api/clusters/{cluster_id}/nodes/{node_id} ───────────────────────────────────────────────────

@router.get("/{cluster_id}/nodes/{node_id}")
async def get_node(cluster_id: int, node_id: int) -> dict:
    """Full config + live state for a single node."""
    node = _fetch_node(cluster_id, node_id)
    live = live_node_states.get(cluster_id, {}).get(node_id)
    return {
        "id":             node["id"],
        "name":           node["name"],
        "host":           node["host"],
        "port":           node["port"],
        "ssh_port":       node["ssh_port"],
        "ssh_user":       node["ssh_user"],
        "db_user":        node["db_user"],
        "enabled":        bool(node["enabled"]),
        "maintenance":    bool(node["maintenance"]),
        "datacenter_id":  node["datacenter_id"],
        "datacenter_name": node["datacenter_name"],
        "cluster_id":     node["cluster_id"],
        "live":           live.to_dict() if live is not None else None,
    }


# ── PATCH /api/clusters/{cluster_id}/nodes/{node_id} ──────────────────────────────────────────────────────

@router.patch("/{cluster_id}/nodes/{node_id}")
async def patch_node(
        cluster_id: int,
        node_id: int,
        body: NodePatchRequest,
) -> dict:
    _fetch_node(cluster_id, node_id)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = node_id
    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE nodes SET {set_clause} WHERE id = :id"),
            updates,
        )
    return {"accepted": True, "node_id": node_id, **body.model_dump(exclude_none=True)}


# ── GET /api/clusters/{cluster_id}/nodes/{node_id}/test-connection ─────────────────────────

@router.get("/{cluster_id}/nodes/{node_id}/test-connection")
async def test_node_connection(cluster_id: int, node_id: int) -> dict:
    node = _fetch_node(cluster_id, node_id)

    result: dict = {
        "node_id":        node_id,
        "ssh_ok":         False,
        "ssh_latency_ms": None,
        "db_ok":          False,
        "db_latency_ms":  None,
        "error":          None,
    }

    ssh = SSHClient(
        host=node["host"],
        port=int(node["ssh_port"] or 22),
        username=node["ssh_user"] or "root",
    )
    try:
        await asyncio.to_thread(ssh.connect)
        latency = await asyncio.to_thread(ssh.test_connection)
        result["ssh_ok"]         = True
        result["ssh_latency_ms"] = latency
    except SSHError as exc:
        result["error"] = f"SSH: {exc}"
        return result
    finally:
        await asyncio.to_thread(ssh.close)

    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        db_latency = await asyncio.to_thread(db.test_connection)
        result["db_ok"]         = True
        result["db_latency_ms"] = db_latency
    except DBError as exc:
        result["error"] = f"DB: {exc}"
    finally:
        await asyncio.to_thread(db.close)

    return result


# ── GET /api/clusters/{cluster_id}/nodes/{node_id}/innodb-status ─────────────────────────

@router.get("/{cluster_id}/nodes/{node_id}/innodb-status")
async def get_innodb_status(cluster_id: int, node_id: int) -> dict:
    node = _fetch_node(cluster_id, node_id)

    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        rows = await asyncio.to_thread(db.query, "SHOW ENGINE INNODB STATUS")
    except DBError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DB connection failed: {exc}",
        )
    finally:
        await asyncio.to_thread(db.close)

    full_text = ""
    if rows:
        row = rows[0]
        normalised = {k.lower(): v for k, v in row.items()}
        full_text = normalised.get("status", "")

    deadlock_section = _extract_deadlock_section(full_text)
    deadlock_parsed = _parse_deadlock(deadlock_section) if deadlock_section else None

    return {
        "node_id":         node_id,
        "full_status":     full_text,
        "latest_deadlock": deadlock_section,
        "has_deadlock":    deadlock_section is not None,
        "deadlock_parsed": deadlock_parsed,
    }


def _extract_deadlock_section(innodb_text: str) -> str | None:
    match = re.search(
        r"LATEST DETECTED DEADLOCK\n-+\n(.*?)(?=\n-{4,}|\Z)",
        innodb_text,
        re.DOTALL,
    )
    return match.group(1).strip() if match else None


def _parse_deadlock(text: str) -> dict | None:
    """
    (#16) Structured parser for InnoDB LATEST DETECTED DEADLOCK section.

    Пример секции (MariaDB / InnoDB):
    *** (1) TRANSACTION:
    TRANSACTION 421093, ACTIVE 0 sec starting index read
    ...
    *** (1) WAITING FOR THIS LOCK TO BE GRANTED:
    RECORD LOCKS space id 123 page no 5 n bits 72 index PRIMARY of table `mydb`.`orders` ...
    lock_mode X locks rec but not gap waiting
    *** (2) TRANSACTION:
    ...
    *** WE ROLL BACK TRANSACTION (1)

    Возвращает dict или None если распарсить не удалось.
    """
    try:
        result: dict = {
            "ts": None,
            "transaction_a": None,
            "transaction_b": None,
            "victim": None,
        }

        # Timestamp строка обычно первая: "2026-04-10 14:23:01 0x7f..."
        ts_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if ts_match:
            result["ts"] = ts_match.group(1)

        # Разбиваем на блоки транзакций
        trx_blocks = re.split(r"\*\*\* \(\d+\) TRANSACTION:", text)
        # trx_blocks[0] — заголовок/timestamp, [1] — TRX 1, [2] — TRX 2

        transactions = []
        for i, block in enumerate(trx_blocks[1:3], start=1):
            trx: dict = {
                "id": None,
                "query": None,
                "table": None,
                "lock_type": None,
                "lock_mode": None,
                "waiting": None,
            }

            # Transaction ID
            trx_id_match = re.search(r"TRANSACTION (\d+)", block)
            if trx_id_match:
                trx["id"] = trx_id_match.group(1)

            # Query — строка после "MySQL thread id" или после "---TRANSACTION"
            # InnoDB печатает последний SQL после "THE QUERY:"  (MariaDB 10.6+)
            # или перед строкой "---" после заголовка транзакции
            query_match = re.search(
                r"(?:THE QUERY:|query currently executing:|waiting for this lock)"
                r".*?\n(.*?)(?:\n|$)",
                block,
                re.IGNORECASE,
            )
            if not query_match:
                # Fallback: ищем первую SQL-подобную строку
                query_match = re.search(
                    r"\n((?:SELECT|INSERT|UPDATE|DELETE|REPLACE|WITH)\s.+?)(?:\n|$)",
                    block,
                    re.IGNORECASE,
                )
            if query_match:
                trx["query"] = query_match.group(1).strip()[:200]

            # Lock info — ищем блок WAITING FOR THIS LOCK / HOLDS THE LOCK
            lock_block_match = re.search(
                r"\*\*\* \(%d\) (?:WAITING FOR THIS LOCK TO BE GRANTED|HOLDS THE LOCK\(S\)):"
                r"(.*?)(?=\*\*\*|\Z)" % i,
                text,
                re.DOTALL,
            )
            if lock_block_match:
                lock_text = lock_block_match.group(1)

                # Table name: `db`.`table`
                table_match = re.search(r"of table `[^`]+`\.`([^`]+)`", lock_text)
                if table_match:
                    trx["table"] = table_match.group(1)

                # Lock type: RECORD LOCKS / TABLE LOCK
                lock_type_match = re.search(r"(RECORD LOCKS|TABLE LOCK)", lock_text, re.IGNORECASE)
                if lock_type_match:
                    trx["lock_type"] = lock_type_match.group(1).upper().replace(" LOCKS", "").replace(" LOCK", "")

                # Lock mode: X, S, X,GAP, X,REC_NOT_GAP ...
                lock_mode_match = re.search(r"lock_mode\s+([\w,]+)", lock_text, re.IGNORECASE)
                if lock_mode_match:
                    trx["lock_mode"] = lock_mode_match.group(1)

                trx["waiting"] = "WAITING FOR THIS LOCK" in text.upper() and bool(
                    re.search(r"\*\*\* \(%d\) WAITING FOR THIS LOCK" % i, text)
                )

            transactions.append(trx)

        if len(transactions) >= 1:
            result["transaction_a"] = transactions[0]
        if len(transactions) >= 2:
            result["transaction_b"] = transactions[1]

        # Victim: WE ROLL BACK TRANSACTION (N)
        victim_match = re.search(r"WE ROLL BACK TRANSACTION \((\d+)\)", text)
        if victim_match:
            victim_idx = int(victim_match.group(1))
            victim_trx = transactions[victim_idx - 1] if victim_idx - 1 < len(transactions) else None
            result["victim"] = victim_trx["id"] if victim_trx else None

        # Если не нашли ни одной транзакции — возвращаем None (fallback на raw)
        if result["transaction_a"] is None and result["transaction_b"] is None:
            return None

        return result

    except Exception:
        logger.debug("_parse_deadlock failed, returning None for fallback", exc_info=True)
        return None


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/actions ───────────────────────────────

@router.post("/{cluster_id}/nodes/{node_id}/actions")
async def node_action(
        cluster_id: int,
        node_id: int,
        body: NodeActionRequest,
) -> dict:
    node = _fetch_node(cluster_id, node_id)

    if not bool(node["enabled"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node {node_id} is disabled — cannot execute actions on it",
        )

    action = body.action

    if action in SYNC_ACTIONS:
        return await _run_sync_action(cluster_id, node, action)
    else:
        return await _start_async_action(cluster_id, node, action)


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/rejoin ───────────────────────────────

@router.post("/{cluster_id}/nodes/{node_id}/rejoin")
async def rejoin_node(cluster_id: int, node_id: int) -> dict:
    """
    Быстрый rejoin одной ноды: systemctl restart mariadb через SSH.
    Возвращает wsrep_cluster_status и wsrep_connected до и после рестарта.
    """
    node = _fetch_node(cluster_id, node_id)

    if not bool(node["enabled"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node {node_id} is disabled",
        )

    before = await _get_wsrep_snapshot(node)

    ssh = SSHClient(
        host=node["host"],
        port=int(node["ssh_port"] or 22),
        username=node["ssh_user"] or "root",
    )
    try:
        await asyncio.to_thread(ssh.connect)
        await asyncio.to_thread(ssh.execute, "systemctl restart mariadb", True)
    except SSHError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SSH error on '{node['name']}': {exc}",
        )
    finally:
        await asyncio.to_thread(ssh.close)

    await asyncio.sleep(10)
    after = await _get_wsrep_snapshot(node)

    write_event(
        level="INFO",
        cluster_id=cluster_id,
        node_id=node_id,
        source="ui",
        message=(
            f"Node '{node['name']}': rejoin executed. "
            f"before={before}, after={after}"
        ),
    )

    asyncio.create_task(
        poll_single_node(cluster_id, node),
        name=f"poll_after_rejoin_{node_id}",
    )

    return {
        "ok":      True,
        "node_id": node_id,
        "before":  before,
        "after":   after,
    }


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/desync ───────────────────────────────

@router.post("/{cluster_id}/nodes/{node_id}/desync")
async def desync_node(cluster_id: int, node_id: int) -> dict:
    node = _fetch_node(cluster_id, node_id)

    if not bool(node["enabled"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node {node_id} is disabled",
        )

    await _db_exec(node, "SET GLOBAL wsrep_desync = ON")

    write_event(
        level="WARN",
        cluster_id=cluster_id,
        node_id=node_id,
        source="ui",
        message=f"Node '{node['name']}': SET GLOBAL wsrep_desync = ON (desync enabled)",
    )

    asyncio.create_task(
        poll_single_node(cluster_id, node),
        name=f"poll_after_desync_{node_id}",
    )

    return {"ok": True, "node_id": node_id, "wsrep_desync": True}


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/resync ───────────────────────────────

@router.post("/{cluster_id}/nodes/{node_id}/resync")
async def resync_node(cluster_id: int, node_id: int) -> dict:
    node = _fetch_node(cluster_id, node_id)

    if not bool(node["enabled"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node {node_id} is disabled",
        )

    await _db_exec(node, "SET GLOBAL wsrep_desync = OFF")

    write_event(
        level="INFO",
        cluster_id=cluster_id,
        node_id=node_id,
        source="ui",
        message=f"Node '{node['name']}': SET GLOBAL wsrep_desync = OFF (resync)",
    )

    asyncio.create_task(
        poll_single_node(cluster_id, node),
        name=f"poll_after_resync_{node_id}",
    )

    return {"ok": True, "node_id": node_id, "wsrep_desync": False}


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/purge-binary-logs ────────────────────

@router.post("/{cluster_id}/nodes/{node_id}/purge-binary-logs")
async def purge_binary_logs(
        cluster_id: int,
        node_id: int,
        body: PurgeBinaryLogsRequest,
) -> dict:
    node = _fetch_node(cluster_id, node_id)

    sql = f"PURGE BINARY LOGS BEFORE '{body.before_date}'"

    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        await asyncio.to_thread(db.execute, sql)
    except DBError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PURGE BINARY LOGS failed on '{node['name']}': {exc}",
        )
    finally:
        await asyncio.to_thread(db.close)

    write_event(
        level="WARN",
        cluster_id=cluster_id,
        node_id=node_id,
        source="ui",
        message=(
            f"Node '{node['name']}': {sql} "
            f"(mode={body.mode})"
        ),
    )

    return {
        "ok":             True,
        "query_executed": sql,
        "node_name":      node["name"],
    }


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/flush (вне MVP) ───────────────────────

@router.post("/{cluster_id}/nodes/{node_id}/flush")
async def flush_node(
        cluster_id: int,
        node_id: int,
        body: FlushRequest,
) -> dict:
    """
    (вне MVP) Выполняет FLUSH-операцию на целевой ноде.

    operation:
      - 'logs'             → FLUSH LOGS
      - 'tables_read_lock' → FLUSH TABLES WITH READ LOCK
      - 'unlock_tables'    → UNLOCK TABLES
    """
    node = _fetch_node(cluster_id, node_id)

    if not bool(node["enabled"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node {node_id} is disabled",
        )

    sql = FLUSH_SQL_MAP[body.operation]

    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        await asyncio.to_thread(db.execute, sql)
    except DBError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{sql} failed on '{node['name']}': {exc}",
        )
    finally:
        await asyncio.to_thread(db.close)

    log_level = "WARN" if body.operation in ("tables_read_lock", "unlock_tables") else "INFO"
    write_event(
        level=log_level,
        cluster_id=cluster_id,
        node_id=node_id,
        source="ui",
        message=f"Node '{node['name']}': {sql}",
    )

    return {
        "ok":             True,
        "node_id":        node_id,
        "node_name":      node["name"],
        "operation":      body.operation,
        "query_executed": sql,
    }


# ── POST /api/clusters/{cluster_id}/nodes/{node_id}/restart-sst (вне MVP) ─────────────────

@router.post("/{cluster_id}/nodes/{node_id}/restart-sst")
async def restart_sst(
        cluster_id: int,
        node_id: int,
) -> dict:
    """
    (вне MVP) Перезапуск MariaDB через SSH для разблокировки застрявшего SST.
    """
    node = _fetch_node(cluster_id, node_id)

    if not bool(node["enabled"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node {node_id} is disabled",
        )

    live = live_node_states.get(cluster_id, {}).get(node_id)
    if live is None or (live.wsrep_local_state_comment or "").upper() not in SST_STUCK_STATES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Node '{node['name']}' is not in an SST state "
                f"(current: {live.wsrep_local_state_comment if live else 'unknown'})"
            ),
        )

    ssh = SSHClient(
        host=node["host"],
        port=int(node["ssh_port"] or 22),
        username=node["ssh_user"] or "root",
    )
    try:
        await asyncio.to_thread(ssh.connect)
        await asyncio.to_thread(ssh.execute, "systemctl restart mariadb", True)
    except SSHError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SSH error on '{node['name']}': {exc}",
        )
    finally:
        await asyncio.to_thread(ssh.close)

    write_event(
        level="WARN",
        cluster_id=cluster_id,
        node_id=node_id,
        source="ui",
        message=(
            f"Node '{node['name']}': restart-sst executed "
            f"(state was {live.wsrep_local_state_comment})"
        ),
    )

    asyncio.create_task(
        poll_single_node(cluster_id, node),
        name=f"poll_after_restart_sst_{node_id}",
    )

    return {
        "ok":      True,
        "node_id": node_id,
        "message": f"systemctl restart mariadb executed on '{node['name']}'",
    }


# ── GET /api/clusters/{cluster_id}/operations/active ────────────────────────────────────────────

@router.get("/{cluster_id}/operations/active")
async def get_active_op(cluster_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    active = await asyncio.to_thread(get_active_operation, cluster_id)
    return {"operation": active}


# ── POST /api/clusters/{cluster_id}/operations/cancel ───────────────────────────────────────────

@router.post("/{cluster_id}/operations/cancel")
async def cancel_operation(cluster_id: int) -> dict:
    _assert_cluster_exists(cluster_id)
    op = await asyncio.to_thread(request_cancel, cluster_id)
    write_event(
        level="INFO",
        cluster_id=cluster_id,
        operation_id=op["id"],
        source="ui",
        message=f"Cancel requested for operation id={op['id']} type={op['type']}",
    )
    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_cancel_requested",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload":    {"operation_id": op["id"]},
    })
    return {"accepted": True, "operation": op}


# ── Helpers ──────────────────────────────────────────────────────────────────────────

async def _get_wsrep_snapshot(node: dict) -> dict:
    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        rows = await asyncio.to_thread(
            db.query,
            "SHOW GLOBAL STATUS WHERE Variable_name IN "
            "('wsrep_cluster_status','wsrep_connected','wsrep_local_state_comment')",
        )
        result = {r["Variable_name"]: r["Value"] for r in rows}
        return {
            "wsrep_cluster_status":      result.get("wsrep_cluster_status"),
            "wsrep_connected":           result.get("wsrep_connected"),
            "wsrep_local_state_comment": result.get("wsrep_local_state_comment"),
        }
    except DBError:
        return {
            "wsrep_cluster_status":      None,
            "wsrep_connected":           None,
            "wsrep_local_state_comment": None,
        }
    finally:
        await asyncio.to_thread(db.close)


async def _run_sync_action(cluster_id: int, node: dict, action: str) -> dict:
    node_id = node["id"]

    if action == "set-readonly":
        await _db_exec(node, "SET GLOBAL read_only = ON")
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': SET GLOBAL read_only = ON",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    if action == "set-readwrite":
        await _db_exec(node, "SET GLOBAL read_only = OFF")
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': SET GLOBAL read_only = OFF",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    if action == "enter-maintenance":
        await _db_exec(node, "SET GLOBAL read_only = ON")
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE nodes SET maintenance = 1 WHERE id = :id"),
                {"id": node_id},
            )
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': entered maintenance mode",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    if action == "exit-maintenance":
        live = live_node_states.get(cluster_id, {}).get(node_id)
        if live and live.maintenance_drift:
            logger.warning(
                "exit-maintenance on node %d: maintenance_drift=True "
                "(read_only already OFF in MariaDB)", node_id,
            )
        await _db_exec(node, "SET GLOBAL read_only = OFF")
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE nodes SET maintenance = 0 WHERE id = :id"),
                {"id": node_id},
            )
        write_event(
            level="INFO", cluster_id=cluster_id, node_id=node_id,
            source="ui", message=f"Node '{node['name']}': exited maintenance mode",
        )
        return {"accepted": True, "action": action, "node_id": node_id}

    raise HTTPException(status_code=500, detail=f"Unhandled sync action: {action}")


async def _db_exec(node: dict, sql: str) -> None:
    db = DBClient(
        host=node["host"],
        port=int(node["port"] or 3306),
        user=node["db_user"] or "root",
        encrypted_password=node["db_password"] or "",
    )
    try:
        await asyncio.to_thread(db.connect)
        await asyncio.to_thread(db.execute, sql)
    except DBError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DB command failed: {exc}",
        )
    finally:
        await asyncio.to_thread(db.close)


async def _start_async_action(cluster_id: int, node: dict, action: str) -> dict:
    await asyncio.to_thread(assert_no_active_operation, cluster_id)

    op_id = await asyncio.to_thread(
        create_operation,
        cluster_id=cluster_id,
        op_type="node_action",
        target_node_id=node["id"],
        details={"action": action, "node_name": node["name"]},
        created_by="api",
    )

    write_event(
        level="INFO",
        cluster_id=cluster_id,
        node_id=node["id"],
        source="ui",
        operation_id=op_id,
        message=f"Node '{node['name']}': async action '{action}' queued (op_id={op_id})",
    )

    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_started",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload": {
            "operation_id": op_id,
            "type":         "node_action",
            "action":       action,
            "node_id":      node["id"],
            "node_name":    node["name"],
        },
    })

    asyncio.create_task(
        _execute_node_action(cluster_id, node, action, op_id),
        name=f"node_action_{op_id}",
    )

    return {
        "accepted":     True,
        "action":       action,
        "node_id":      node["id"],
        "operation_id": op_id,
        "status":       "pending",
    }


async def _execute_node_action(
        cluster_id: int,
        node: dict,
        action: str,
        op_id: int,
) -> None:
    node_id   = node["id"]
    node_name = node["name"]

    await asyncio.to_thread(set_operation_status, op_id, "running")

    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_progress",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload":    {"operation_id": op_id, "message": f"Executing '{action}' on {node_name}"},
    })

    if await asyncio.to_thread(is_cancel_requested, op_id):
        await asyncio.to_thread(set_operation_status, op_id, "cancelled")
        await _broadcast_op_finished(cluster_id, op_id, "cancelled")
        return

    try:
        await asyncio.to_thread(_ssh_node_action, node, action)
    except SSHError as exc:
        error_msg = f"SSH error during '{action}' on '{node_name}': {exc}"
        logger.error(error_msg)
        write_event(
            level="ERROR", cluster_id=cluster_id, node_id=node_id,
            source="ssh", operation_id=op_id, message=error_msg,
        )
        await asyncio.to_thread(set_operation_status, op_id, "failed", error_msg)
        await _broadcast_op_finished(cluster_id, op_id, "failed", error_msg)
        await _safe_poll_node(cluster_id, node)
        return
    except Exception as exc:
        error_msg = f"Unexpected error during '{action}' on '{node_name}': {exc}"
        logger.exception(error_msg)
        write_event(
            level="ERROR", cluster_id=cluster_id, node_id=node_id,
            source="system", operation_id=op_id, message=error_msg,
        )
        await asyncio.to_thread(set_operation_status, op_id, "failed", error_msg)
        await _broadcast_op_finished(cluster_id, op_id, "failed", error_msg)
        await _safe_poll_node(cluster_id, node)
        return

    write_event(
        level="INFO", cluster_id=cluster_id, node_id=node_id,
        source="ui", operation_id=op_id,
        message=f"Node '{node_name}': action '{action}' completed successfully",
    )
    await asyncio.to_thread(set_operation_status, op_id, "success")
    await _broadcast_op_finished(cluster_id, op_id, "success")
    await _safe_poll_node(cluster_id, node)


async def _safe_poll_node(cluster_id: int, node: dict) -> None:
    try:
        await poll_single_node(cluster_id, node)
    except Exception as exc:
        logger.warning("post-action poll failed for node %d: %s", node["id"], exc)


def _ssh_node_action(node: dict, action: str) -> None:
    ssh = SSHClient(
        host=node["host"],
        port=int(node["ssh_port"] or 22),
        username=node["ssh_user"] or "root",
    )
    ssh.connect()
    try:
        if action == "start":
            ssh.execute("systemctl start mariadb", check=True)
        elif action == "stop":
            ssh.execute("systemctl stop mariadb", check=True)
        elif action == "restart":
            ssh.execute("systemctl restart mariadb", check=True)
        elif action == "rejoin-force":
            ssh.execute("systemctl stop mariadb", check=True)
            ssh.execute(
                "sed -i 's/^safe_to_bootstrap:.*$/safe_to_bootstrap: 0/' "
                "/var/lib/mysql/grastate.dat",
                check=True,
            )
            ssh.execute("systemctl start mariadb", check=True)
        else:
            raise SSHError(f"Unknown async action: {action}")
    finally:
        ssh.close()


async def _broadcast_op_finished(
        cluster_id: int,
        op_id: int,
        final_status: str,
        error: str | None = None,
) -> None:
    payload: dict = {"operation_id": op_id, "status": final_status}
    error and payload.update({"error": error})
    await ws_manager.broadcast(cluster_id, {
        "event":      "operation_finished",
        "cluster_id": cluster_id,
        "ts":         datetime.now(timezone.utc).isoformat(),
        "payload":    payload,
    })
