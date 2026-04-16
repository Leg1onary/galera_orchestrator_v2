"""
Backup router — Backup Center v1.

ТЗ Backup Center v1:
  GET /api/clusters/{cluster_id}/backup/scan?server_id={id}

Scan — SSH into backup server, list files in backup_dir, return typed file list.
No write operations (запуск, удаление, restore) — review-only scope.
"""
from __future__ import annotations

import logging
import shlex
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database import engine, get_cluster_or_404
from dependencies import require_auth
from services.ssh_client import SSHClient, SSHError
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/clusters",
    tags=["backup"],
    dependencies=[Depends(require_auth)],
)


# ── Response model helpers ────────────────────────────────────────────────────

def _classify_file(filename: str) -> tuple[str, str]:
    """
    Returns (type, tool) tuple.
    type:  full | schema-only | unknown
    tool:  mysqldump | mariabackup | unknown
    """
    base = filename.lower()

    # type
    if base.startswith("full_"):
        ftype = "full"
    elif base.startswith("schema_"):
        ftype = "schema-only"
    else:
        ftype = "unknown"

    # tool
    if base.endswith(".sql.gz"):
        tool = "mysqldump"
    elif ".xbstream" in base:
        tool = "mariabackup"
    else:
        tool = "unknown"

    return ftype, tool


def _parse_find_output(raw: str) -> list[dict]:
    """
    Parse output of:
      find {dir} -maxdepth 1 -type f -printf '%f\t%s\t%TY-%Tm-%TdT%TH:%TM:%TS\n'

    Returns list of file dicts. Skips malformed lines.
    """
    files = []
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        filename, size_raw, modified_raw = parts

        try:
            size_bytes = int(size_raw)
        except ValueError:
            size_bytes = 0

        # Normalize timestamp: truncate subseconds and append Z
        # Format from find: 2026-04-16T03:47:22.123456789
        ts_str = modified_raw.split(".")[0]  # drop fractional seconds
        try:
            modified_at = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=timezone.utc
            ).isoformat()
        except ValueError:
            modified_at = None

        ftype, tool = _classify_file(filename)

        files.append(
            {
                "filename":    filename,
                "type":        ftype,
                "tool":        tool,
                "size_bytes":  size_bytes,
                "modified_at": modified_at,
            }
        )

    # Sort by modified_at desc (most recent first)
    files.sort(key=lambda f: f["modified_at"] or "", reverse=True)
    return files


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/{cluster_id}/backup/scan")
async def scan_backup_server(
    cluster_id: int,
    server_id:  int = Query(..., description="Backup server ID to scan"),
) -> dict:
    """
    Scan backup directory on a backup server via SSH.
    Returns list of typed backup files.
    """
    # 1. Verify cluster exists
    get_cluster_or_404(cluster_id)

    # 2. Find backup_server and verify it belongs to this cluster
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, cluster_id, name, host, ssh_port, ssh_user, backup_dir, enabled "
                "FROM backup_servers WHERE id = :sid"
            ),
            {"sid": server_id},
        ).mappings().fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Backup server {server_id} not found")

    srv = dict(row)

    if srv["cluster_id"] != cluster_id:
        raise HTTPException(
            status_code=404,
            detail=f"Backup server {server_id} does not belong to cluster {cluster_id}",
        )

    # 3. Reject disabled servers
    if not srv["enabled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Backup server '{srv['name']}' is disabled. Enable it in Settings first.",
        )

    backup_dir = srv["backup_dir"]

    # 4 + 5. SSH connect and list directory
    cmd = (
        f"find {shlex.quote(backup_dir)} -maxdepth 1 -type f "
        f"-printf '%f\\t%s\\t%TY-%Tm-%TdT%TH:%TM:%TS\\n'"
    )

    try:
        with SSHClient(host=srv["host"], port=srv["ssh_port"], username=srv["ssh_user"]) as ssh:
            stdout, stderr = ssh.execute(cmd)
    except SSHError as exc:
        logger.warning("Backup scan SSH error [server_id=%d]: %s", server_id, exc)
        raise HTTPException(
            status_code=502,
            detail=f"SSH error connecting to backup server '{srv['name']}' ({srv['host']}): {exc}",
        )

    # Directory not found: find exits 1 + "No such file or directory" in stderr
    if stderr and "no such file or directory" in stderr.lower():
        raise HTTPException(
            status_code=502,
            detail=f"Backup directory '{backup_dir}' not found on '{srv['name']}' ({srv['host']})",
        )

    # 6 + 7. Parse and return
    files = _parse_find_output(stdout)

    return {
        "server_id":  server_id,
        "backup_dir": backup_dir,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "files":      files,
    }
