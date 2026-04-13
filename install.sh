#!/bin/bash
# =============================================================================
# Galera Orchestrator v2 — One-line installer
# Использование:
#   curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/install.sh -o /tmp/install.sh && bash /tmp/install.sh
# =============================================================================

set -eu

REPO_RAW="https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master"
INSTALL_DIR="${INSTALL_DIR:-$HOME/galera-orchestrator}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()   { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()     { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()   { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()  { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
prompt() { echo -e "${BOLD}$*${NC}"; }

# read_tty VAR — читает строку напрямую с /dev/tty (работает в прямом запуске)
read_tty()  { read -r  "$1" < /dev/tty; }
read_pass() { read -rs "$1" < /dev/tty; echo ""; }

echo -e ""
echo -e "${BOLD}${CYAN}██████╗ █████╗ ██╗     ███████╗██████╗  █████╗ ${NC}"
echo -e "${BOLD}${CYAN}██╔════╝ ██╔══██╗██║     ██╔════╝██╔══██╗██╔══██╗${NC}"
echo -e "${BOLD}${CYAN}██║  ███╗███████║██║     █████╗  █████╔╝███████║${NC}"
echo -e "${BOLD}${CYAN}██║   ██║██╔══██║██║     ██╔══╝  ██╔══██╗██╔══██║${NC}"
echo -e "${BOLD}${CYAN}╚██████╔╝██║  ██║██████╗███████╗██║  ██║██║  ██║${NC}"
echo -e "${BOLD}${CYAN} ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝${NC}"
echo -e "${BOLD}        Orchestrator v2 — Installer${NC}"
echo -e ""

# ─── 1. Проверка зависимостей
info "Проверяю наличие Docker..."
command -v docker >/dev/null 2>&1 || error "Docker не установлен."
docker compose version >/dev/null 2>&1 || error "Docker Compose v2 не найден."
ok "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
ok "Docker Compose $(docker compose version --short)"

# ─── 2. Директория
info "Инсталляция в ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cd "${INSTALL_DIR}"

# ─── 3. Скачиваем файлы
info "Скачиваю docker-compose.ghcr.yml..."
curl -fsSL "${REPO_RAW}/docker-compose.ghcr.yml" -o docker-compose.ghcr.yml
ok "docker-compose.ghcr.yml скачан"
echo ""

# ─── 4. Настройка .env
echo -e "${BOLD}────────────────────────────────────────${NC}"
echo -e "${BOLD}  Настройка конфигурации${NC}"
echo -e "${BOLD}────────────────────────────────────────${NC}"
echo ""

prompt "👤 Admin username [admin]:"
read_tty ADMIN_USERNAME
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"

prompt "🔐 Admin password:"
read_pass ADMIN_PASSWORD
if test -z "$ADMIN_PASSWORD"; then
    error "Admin password не может быть пустым"
fi

echo ""
prompt "🔑 Путь к SSH-ключу [по умолчанию: $HOME/.ssh/id_rsa]:"
read_tty SSH_KEY_INPUT
if test -z "$SSH_KEY_INPUT"; then
    SSH_KEY_PATH="$HOME/.ssh/id_rsa"
else
    SSH_KEY_PATH=$(echo "$SSH_KEY_INPUT" | sed "s|^~|$HOME|g")
fi
if test ! -f "$SSH_KEY_PATH"; then
    warn "Файл ключа не найден: $SSH_KEY_PATH (проверь путь после запуска)"
fi

echo ""
prompt "🌐 Порт панели [8000]:"
read_tty HOST_PORT
if test -z "$HOST_PORT"; then
    HOST_PORT="8000"
fi

# Генерируем секреты
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
FERNET_SECRET=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)

printf '%s\n' \
    "# Сгенерировано install.sh $(date '+%Y-%m-%d %H:%M:%S')" \
    "" \
    "HOST_PORT=$HOST_PORT" \
    "" \
    "ADMIN_USERNAME=$ADMIN_USERNAME" \
    "ADMIN_PASSWORD=$ADMIN_PASSWORD" \
    "" \
    "JWT_SECRET_KEY=$JWT_SECRET" \
    "FERNET_SECRET_KEY=$FERNET_SECRET" \
    "" \
    "SSH_KEY_PATH=$SSH_KEY_PATH" \
    "SSH_CONNECT_TIMEOUT=5" \
    "SSH_COMMAND_TIMEOUT=10" \
    "" \
    "DATABASE_URL=sqlite:////data/orchestrator.db" \
    "DB_CONNECT_TIMEOUT=3" \
    > .env

chmod 600 .env
ok ".env создан (chmod 600)"

# ─── 5. Запуск
echo ""
info "Тяну Docker-образ и запускаю..."
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up -d

echo ""
echo -e "${GREEN}${BOLD}────────────────────────────────────────${NC}"
echo -e "${GREEN}${BOLD}  ✅  Установка завершена!${NC}"
echo -e "${GREEN}${BOLD}────────────────────────────────────────${NC}"
echo ""
echo -e "  🌍 Панель:  ${BOLD}http://$(hostname -I | awk '{print $1}'):$HOST_PORT${NC}"
echo -e "  👤 Логин:  ${BOLD}$ADMIN_USERNAME${NC}"
echo -e "  📁 Каталог: ${BOLD}${INSTALL_DIR}${NC}"
echo ""
echo -e "  🔄 Обновление в будущем:"
echo -e "     ${CYAN}bash ${INSTALL_DIR}/update.sh${NC}"
echo ""
echo -e "  📜 Логи:"
echo -e "     ${CYAN}docker logs -f galera-orchestrator${NC}"
echo ""
