#!/usr/bin/env bash
# ============================================================
#  Galera Orchestrator v2 — update script
#  Использование:
#    bash ~/galera-orchestrator/update.sh
#  Или напрямую:
#    curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/update.sh | bash
# ============================================================
set -euo pipefail

# ─── colors ──────────────────────────────────────────────────
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m"

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

echo -e ""
echo -e "${BOLD}  Galera Orchestrator v2 — Updater${NC}"
echo -e "  https://github.com/Leg1onary/galera_orchestrator_v2"
echo -e ""

# ─── locate install dir ──────────────────────────────────────
# Если скрипт запущен из директории установки — используем её.
# Иначе — пробуем дефолт ~/galera-orchestrator.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$(pwd)}")" 2>/dev/null && pwd || echo "")"
if [ -f "${SCRIPT_DIR}/docker-compose.ghcr.yml" ]; then
    INSTALL_DIR="${SCRIPT_DIR}"
else
    INSTALL_DIR="${HOME}/galera-orchestrator"
fi

if [ ! -f "${INSTALL_DIR}/docker-compose.ghcr.yml" ]; then
    error "Файл docker-compose.ghcr.yml не найден в ${INSTALL_DIR}.\n  Укажи директорию вручную: INSTALL_DIR=/path/to/dir bash update.sh"
fi

if [ ! -f "${INSTALL_DIR}/.env" ]; then
    error ".env не найден в ${INSTALL_DIR}. Похоже установка не завершена."
fi

info "Директория установки: ${INSTALL_DIR}"
cd "${INSTALL_DIR}"

# ─── check docker ────────────────────────────────────────────
command -v docker &>/dev/null   || error "Docker не найден."
docker compose version &>/dev/null || error "Docker Compose v2 не найден."

# ─── show current state ──────────────────────────────────────
CURRENT_IMAGE=$(docker compose -f docker-compose.ghcr.yml images --format json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('Tag','unknown') if d else 'unknown')" 2>/dev/null \
    || echo "unknown")
info "Текущий тег образа: ${CURRENT_IMAGE}"

# ─── backup reminder ─────────────────────────────────────────
warn "Перед обновлением рекомендуется сделать бэкап БД:"
echo -e "  ${CYAN}docker run --rm -v orchestrator-data:/data -v \"\$(pwd)\":/backup alpine \\"
echo -e "    tar czf /backup/orchestrator-db-\$(date +%Y%m%d-%H%M%S).tar.gz /data${NC}"
echo ""
echo -e "${BOLD}[?]${NC} Продолжить обновление? [Y/n]: "
read -r CONFIRM
CONFIRM="${CONFIRM:-Y}"
[[ "${CONFIRM}" =~ ^[Yy] ]] || { info "Отменено."; exit 0; }

# ─── pull new image ──────────────────────────────────────────
echo ""
info "Тяну новый образ с GHCR..."
docker compose -f docker-compose.ghcr.yml pull
ok "Образ обновлён"

# ─── restart container ───────────────────────────────────────
info "Перезапускаю контейнер..."
docker compose -f docker-compose.ghcr.yml up -d --remove-orphans
ok "Контейнер перезапущен"

# ─── also update compose file itself ────────────────────────
info "Обновляю docker-compose.ghcr.yml из репозитория..."
RAW="https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master"
curl -fsSL "${RAW}/docker-compose.ghcr.yml" -o docker-compose.ghcr.yml
ok "docker-compose.ghcr.yml обновлён"

# ─── show result ─────────────────────────────────────────────
NEW_IMAGE=$(docker compose -f docker-compose.ghcr.yml images --format json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('Tag','unknown') if d else 'unknown')" 2>/dev/null \
    || echo "unknown")

HOST_PORT=$(grep '^HOST_PORT=' .env | cut -d= -f2 | tr -d '[:space:]' || echo "8000")

echo ""
echo -e "${GREEN}${BOLD}  ✅  Обновление завершено!${NC}"
echo -e ""
echo -e "  🌍 Панель:     ${BOLD}http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost'):${HOST_PORT}${NC}"
echo -e "  📁 Директория: ${BOLD}${INSTALL_DIR}${NC}"
echo -e "  📋 Логи:       ${CYAN}docker logs -f galera-orchestrator${NC}"
echo ""
