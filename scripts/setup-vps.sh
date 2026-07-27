#!/usr/bin/env bash
# =============================================================================
# scripts/setup-vps.sh
# Hardening basico de un VPS Linux (Ubuntu 22.04+ / Debian 12+) para
# alojar el proyecto ITS RAG Math.
#
# Que hace:
#   1. Actualiza el sistema operativo
#   2. Instala Docker Engine + Docker Compose v2
#   3. Configura el firewall (UFW): solo 22, 80, 443
#   4. Instala y configura fail2ban contra brute-force SSH
#   5. Refuerza la configuracion SSH (deshabilita root login, password auth)
#   6. Configura actualizaciones automaticas de seguridad
#   7. Crea un usuario 'deploy' no-root para correr la app (recomendado)
#
# IMPORTANTE: ejecutar como root o con sudo.
#
# Uso:
#   sudo ./scripts/setup-vps.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log()  { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Verificar root
if [ "$EUID" -ne 0 ]; then
    fail "Este script debe ejecutarse como root. Usa: sudo $0"
fi

# Detectar distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    fail "No se puede detectar la distribucion Linux."
fi

log "Distribucion detectada: $DISTRO $VERSION_ID"

if [[ "$DISTRO" != "ubuntu" && "$DISTRO" != "debian" ]]; then
    fail "Este script soporta solo Ubuntu o Debian."
fi

# --- 1. Actualizar el sistema --------------------------------------------
log "[1/7] Actualizando el sistema..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    ufw \
    fail2ban \
    unattended-upgrades \
    apt-listchanges

# --- 2. Instalar Docker ----------------------------------------------------
log "[2/7] Instalando Docker..."

if ! command -v docker >/dev/null 2>&1; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/${DISTRO}/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${DISTRO} \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    log "Docker instalado: $(docker --version)"
else
    log "Docker ya esta instalado: $(docker --version)"
fi

# Verificar Docker Compose v2
if ! docker compose version >/dev/null 2>&1; then
    fail "Docker Compose v2 no esta disponible. Actualiza Docker."
fi
log "Docker Compose: $(docker compose version)"

# --- 3. Configurar firewall (UFW) ----------------------------------------
log "[3/7] Configurando firewall UFW..."

ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# SSH
ufw allow 22/tcp comment "SSH"

# HTTP y HTTPS (para Caddy + Let's Encrypt)
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"

# Activar UFW (--force evita el prompt interactivo)
ufw --force enable
ufw status verbose

# --- 4. Configurar fail2ban ----------------------------------------------
log "[4/7] Configurando fail2ban..."

cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
# Banear por 1 hora tras 5 intentos fallidos
bantime  = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port    = ssh
filter  = sshd
logpath = %(sshd_log)s
backend = %(sshd_backend)s
EOF

systemctl enable fail2ban
systemctl restart fail2ban
log "fail2ban configurado: $(fail2ban-client status sshd 2>&1 | head -3)"

# --- 5. Refuerza SSH -----------------------------------------------------
log "[5/7] Reforzando configuracion SSH..."

SSHD_CONFIG="/etc/ssh/sshd_config"
SSHD_BACKUP="${SSHD_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"

cp "$SSHD_CONFIG" "$SSHD_BACKUP"
log "Backup de sshd_config: $SSHD_BACKUP"

# Funciones helper
set_sshd() {
    local key="$1"
    local value="$2"
    if grep -qE "^\s*#?\s*${key}\s" "$SSHD_CONFIG"; then
        sed -i "s|^\s*#\?\s*${key}\s.*|${key} ${value}|" "$SSHD_CONFIG"
    else
        echo "${key} ${value}" >> "$SSHD_CONFIG"
    fi
}

set_sshd "PermitRootLogin" "no"
set_sshd "PasswordAuthentication" "no"
set_sshd "PubkeyAuthentication" "yes"
set_sshd "PermitEmptyPasswords" "no"
set_sshd "X11Forwarding" "no"
set_sshd "ClientAliveInterval" "300"
set_sshd "ClientAliveCountMax" "2"

# Validar config antes de reiniciar
sshd -t && {
    systemctl restart sshd
    log "SSH reforzado y reiniciado."
} || {
    warn "Configuracion SSH invalida. Revirtiendo..."
    cp "$SSHD_BACKUP" "$SSHD_CONFIG"
}

# --- 6. Actualizaciones automaticas ---------------------------------------
log "[6/7] Configurando actualizaciones automaticas de seguridad..."

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

# Reiniciar servicio
systemctl enable unattended-upgrades
systemctl restart unattended-upgrades
log "Actualizaciones automaticas configuradas."

# --- 7. Crear usuario 'deploy' -----------------------------------------
log "[7/7] Creando usuario 'deploy'..."

if ! id "deploy" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" deploy
    mkdir -p /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    # Copiar authorized_keys de root si existe
    if [ -f /root/.ssh/authorized_keys ]; then
        cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
        chown -R deploy:deploy /home/deploy/.ssh
        chmod 600 /home/deploy/.ssh/authorized_keys
        log "Claves SSH copiadas de root a deploy."
    else
        warn "No hay /root/.ssh/authorized_keys. Agrega tu clave publica manualmente a /home/deploy/.ssh/authorized_keys"
    fi
    # Agregar al grupo docker
    usermod -aG docker deploy
    log "Usuario 'deploy' creado y agregado al grupo docker."
else
    log "Usuario 'deploy' ya existe."
    usermod -aG docker deploy 2>/dev/null || true
fi

# --- Resumen ------------------------------------------------------------
echo
log "===== SETUP COMPLETADO ====="
log "Sistema: $DISTRO $VERSION_ID"
log "Docker: $(docker --version)"
log "Docker Compose: $(docker compose version)"
log "Firewall:"
ufw status | head -10
echo
log "fail2ban: activo"
log "SSH: login root deshabilitado, password auth deshabilitado"
log "Actualizaciones automaticas: activas"
log "Usuario 'deploy' creado con acceso a Docker"
echo
warn "SIGUIENTE PASO: agrega tu clave SSH publica a /home/deploy/.ssh/authorized_keys"
warn "Luego: desde tu maquina local, ejecuta:"
warn "  ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@IP-DEL-VPS"
warn "Y prueba: ssh deploy@IP-DEL-VPS"
echo
