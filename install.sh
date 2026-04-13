#!/bin/bash
# =============================================================================
# Galera Orchestrator v2 — One-line installer
# Использование:
#   curl -fsSL https://raw.githubusercontent.com/Leg1onary/galera_orchestrator_v2/master/install.sh | bash
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

# ─── 2. Проверка python3 (нужен для bcrypt-хэша и Fernet-ключа)
command -v python3 >/dev/null 2>&1 || error "python3 не найден — требуется для генерации секретов."

# ─── 3. Установка bcrypt если нет
python3 -c "import bcrypt" 2>/dev/null || {
    warn "bcrypt не найден, устанавливаю через pip..."
    python3 -m pip install --quiet bcrypt || error "Не удалось установить bcrypt. Установи вручную: pip install bcrypt"
}

# ─── 4. Директория
info "Инсталляция в ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cd "${INSTALL_DIR}"

# ─── 5. Скачиваем файлы
info "Скачиваю docker-compose.ghcr.yml..."
curl -fsSL "${REPO_RAW}/docker-compose.ghcr.yml" -o docker-compose.ghcr.yml
ok "docker-compose.ghcr.yml скачан"
echo ""

# ─── 6. Настройка .env
echo -e "${BOLD}────────────────────────────────────────${NC}"
echo -e "${BOLD}  Настройка конфигурации${NC}"
echo -e "${BOLD}────────────────────────────────────────${NC}"
echo ""

prompt "👤 Admin username [admin]:"
read_tty ADMIN_USERNAME
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"

prompt "🔐 Admin password:"
read_pass ADMIN_PASSWORD_RAW
if test -z "$ADMIN_PASSWORD_RAW"; then
    error "Admin password не может быть пустым"
fi

# Хэшируем пароль через bcrypt — в .env пишем только хэш, не plaintext
ADMIN_PASSWORD_HASH=$(python3 -c "
import bcrypt, sys
pw = sys.argv[1].encode()
print(bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)).decode())
" "$ADMIN_PASSWORD_RAW")
ok "bcrypt-хэш пароля сгенерирован"

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
HOST_PORT="${HOST_PORT:-8000}"

echo ""
prompt "🔒 Включить COOKIE_SECURE=true? (рекомендуется при работе через HTTPS) [Y/n]:"
read_tty COOKIE_SECURE_INPUT
case "${COOKIE_SECURE_INPUT:-Y}" in
    [nN]*) COOKIE_SECURE="false" ;;
    *)     COOKIE_SECURE="true"  ;;
esac
if [ "$COOKIE_SECURE" = "true" ]; then
    ok "COOKIE_SECURE=true — убедись что панель доступна только через HTTPS"
else
    warn "COOKIE_SECURE=false — JWT-cookie будет отправляться по HTTP (только для dev/тестов)"
fi

# ─── 7. Генерируем секреты
# JWT_SECRET_KEY — hex 32 байта (64 символа)
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null \
    || python3 -c "import secrets; print(secrets.token_hex(32))")

# FERNET_SECRET_KEY — валидный Fernet-ключ (base64url, 32 байта), отличается от JWT
FERNET_SECRET=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

ok "JWT_SECRET_KEY сгенерирован (64 hex-символа)"
ok "FERNET_SECRET_KEY сгенерирован (Fernet)"

# ─── 8. Пишем .env
printf '%s\n' \
    "# Сгенерировано install.sh $(date '+%Y-%m-%d %H:%M:%S')" \
    "# ⚠️  Не коммить этот файл в git!" \
    "" \
    "HOST_PORT=$HOST_PORT" \
    "" \
    "ADMIN_USERNAME=$ADMIN_USERNAME" \
    "# Пароль хранится в виде bcrypt-хэша. Plaintext не сохраняется." \
    "ADMIN_PASSWORD_HASH=$ADMIN_PASSWORD_HASH" \
    "" \
    "# JWT и Fernet ключи должны быть РАЗНЫМИ значениями" \
    "JWT_SECRET_KEY=$JWT_SECRET" \
    "FERNET_SECRET_KEY=$FERNET_SECRET" \
    "" \
    "SSH_KEY_PATH=$SSH_KEY_PATH" \
    "SSH_CONNECT_TIMEOUT=5" \
    "SSH_COMMAND_TIMEOUT=10" \
    "" \
    "DATABASE_URL=sqlite:////data/orchestrator.db" \
    "DB_CONNECT_TIMEOUT=3" \
    "" \
    "# Безопасность" \
    "COOKIE_SECURE=$COOKIE_SECURE" \
    "DOCS_ENABLED=false" \
    > .env

chmod 600 .env
ok ".env создан (chmod 600)"

# ─── 9. Запуск
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
echo -e "  👤 Логин:   ${BOLD}$ADMIN_USERNAME${NC}"
echo -e "  📁 Каталог: ${BOLD}${INSTALL_DIR}${NC}"
if [ "$COOKIE_SECURE" = "true" ]; then
echo -e "  🔒 TLS:     ${YELLOW}${BOLD}COOKIE_SECURE=true — доступ только через HTTPS${NC}"
fi
echo ""
echo -e "  🔄 Обновление:"
echo -e "     ${CYAN}bash ${INSTALL_DIR}/update.sh${NC}"
echo ""
echo -e "  📜 Логи:"
echo -e "     ${CYAN}docker logs -f galera-orchestrator${NC}"
echo ""
