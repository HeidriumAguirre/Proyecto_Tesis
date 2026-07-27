#!/usr/bin/env bash
# =============================================================================
# scripts/deploy.sh
# Despliegue inicial del proyecto ITS RAG Math en un VPS Linux limpio.
#
# Pre-requisitos (ejecutar primero scripts/setup-vps.sh):
#   - Ubuntu 22.04+ / Debian 12+ fresco
#   - Docker Engine + Docker Compose v2 instalados
#   - Usuario no-root con permisos sudo (recomendado)
#   - DNS del dominio apuntando a la IP publica del VPS
#   - Puertos 80 y 443 abiertos en el firewall
#
# Uso:
#   ./scripts/deploy.sh
#
# Despues de ejecutar, la app estara disponible en https://DOMINIO.
# =============================================================================
set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Helpers --------------------------------------------------------------
log()  { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || fail "$1 no esta instalado. Ejecuta setup-vps.sh primero."
}

# --- Validaciones previas ---------------------------------------------------
require_cmd docker
require_cmd git

if ! docker compose version >/dev/null 2>&1; then
    fail "Docker Compose v2 no esta disponible. Instala con: sudo apt install docker-compose-plugin"
fi

# --- Ubicacion del proyecto -------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

log "Directorio del proyecto: $PROJECT_DIR"

# --- Clonar o actualizar repo ------------------------------------------------
if [ ! -d ".git" ]; then
    fail "No estas dentro de un repositorio git. Clona el repo primero: git clone https://github.com/HeidriumAguirre/Proyecto_Tesis.git"
fi

log "Pull de la ultima version..."
git pull --rebase --autostash || warn "No se pudo hacer pull (puede no haber remoto configurado)"

# --- Configurar .env si no existe -----------------------------------------
if [ ! -f ".env" ]; then
    if [ -f ".env.production.example" ]; then
        log "Creando .env desde .env.production.example..."
        cp .env.production.example .env
        warn "EDITA .env y rellena:"
        warn "  - MYSQL_ROOT_PASSWORD (password fuerte)"
        warn "  - GEMINI_API_KEY (de https://aistudio.google.com/app/apikey)"
        warn "  - Caddyfile: cambiar DOMINIO.example.cl y TU-EMAIL@example.cl"
        fail "Edita .env y vuelve a ejecutar."
    else
        fail "No existe .env ni .env.production.example. Crea .env primero."
    fi
fi

# Verificar que el .env tenga las variables criticas
source .env
if [ -z "${GEMINI_API_KEY:-}" ] || [ "$GEMINI_API_KEY" = "TU_API_KEY_AQUI" ]; then
    fail "GEMINI_API_KEY no esta configurada en .env"
fi
if [ -z "${MYSQL_ROOT_PASSWORD:-}" ] || [ "$MYSQL_ROOT_PASSWORD" = "demo" ]; then
    fail "MYSQL_ROOT_PASSWORD no esta configurada o sigue como 'demo'. Cambiala en .env"
fi

# --- Configurar Caddyfile ---------------------------------------------------
if grep -q "DOMINIO.example.cl" Caddyfile 2>/dev/null; then
    warn "Caddyfile aun tiene DOMINIO.example.cl como placeholder."
    warn "Edita Caddyfile y reemplaza por tu dominio real antes de continuar."
    fail "Caddyfile no configurado."
fi

# --- Crear directorios necesarios -------------------------------------------
mkdir -p scripts/backups

# --- Levantar la pila -------------------------------------------------------
log "Deteniendo contenedores previos (si existen)..."
docker compose down --remove-orphans || true

log "Construyendo imagenes..."
docker compose build --no-cache app_tutor

log "Levantando servicios..."
docker compose up -d

log "Esperando a que MySQL este healthy..."
for i in $(seq 1 30); do
    if docker compose ps db_relacional | grep -q "(healthy)"; then
        log "MySQL healthy."
        break
    fi
    if [ "$i" -eq 30 ]; then
        fail "MySQL no alcanzo estado healthy en 5 minutos. Revisa: docker compose logs db_relacional"
    fi
    sleep 10
done

log "Esperando a que app_tutor este up..."
for i in $(seq 1 30); do
    if docker compose ps app_tutor | grep -q "Up "; then
        log "app_tutor up."
        break
    fi
    if [ "$i" -eq 30 ]; then
        fail "app_tutor no arranco en 5 minutos. Revisa: docker compose logs app_tutor"
    fi
    sleep 5
done

log "Esperando a que Caddy obtenga certificado HTTPS..."
for i in $(seq 1 30); do
    if docker compose logs caddy 2>&1 | grep -q "obtained certificate"; then
        log "Caddy obtuvo certificado HTTPS."
        break
    fi
    if [ "$i" -eq 30 ]; then
        warn "Caddy no reporto certificado en 5 minutos. Revisa: docker compose logs caddy"
        break
    fi
    sleep 10
done

# --- Verificacion final ----------------------------------------------------
echo
log "===== ESTADO FINAL ====="
docker compose ps

echo
log "===== URLS DISPONIBLES ====="
DOMAIN=$(grep -E "^[a-zA-Z0-9.-]+\.cl " Caddyfile | head -1 | awk '{print $1}')
if [ -n "$DOMAIN" ]; then
    log "HTTPS: https://$DOMAIN"
    log "HTTP (redirige a HTTPS): http://$DOMAIN"
else
    log "No se pudo extraer el dominio del Caddyfile. Revisalo manualmente."
fi

echo
log "===== PROXIMOS PASOS ====="
log "1. Verifica que https://DOMINIO carga la app correctamente"
log "2. Ingresa con las credenciales seed:"
log "   - Docente: heidrium.aguirre@murialdo.cl / Demo2026!"
log "   - Estudiante: mateo.gonzalez@murialdo.cl (sin contrasena)"
log "3. Ejecuta el seed de datos si la BD esta vacia:"
log "   docker compose exec app_tutor python database/seed.py"
log "4. Configura el backup automatico:"
log "   crontab -e   # agregar linea: 0 3 * * * /ruta/al/proyecto/scripts/backup.sh"
log "5. Monitorea:"
log "   docker compose logs -f"
echo
