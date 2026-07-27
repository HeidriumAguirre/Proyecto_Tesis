#!/usr/bin/env bash
# =============================================================================
# scripts/backup.sh
# Backup automatico de MySQL y ChromaDB del proyecto ITS RAG Math.
#
# Que respalda:
#   - Dump SQL completo de MySQL (mysqldump) -> scripts/backups/db/YYYYMMDD_HHMMSS.sql
#   - Archivo tar.gz del volumen ChromaDB -> scripts/backups/chroma/YYYYMMDD_HHMMSS.tar.gz
#   - Metadatos del backup (fecha, versiones, conteos) -> manifest.json
#
# Retencion: mantiene los ultimos N backups (default 7), borra el resto.
#
# Uso:
#   ./scripts/backup.sh                # backup completo con defaults
#   ./scripts/backup.sh --keep 14      # conserva los ultimos 14
#   ./scripts/backup.sh --upload       # sube el .tar.gz a un S3 / B2 (configurar abajo)
#
# Para programar diariamente a las 3 AM:
#   crontab -e
#   0 3 * * * /opt/its_rag_math/scripts/backup.sh >> /var/log/its_backup.log 2>&1
# =============================================================================
set -euo pipefail

# --- Configuracion --------------------------------------------------------
KEEP=7
UPLOAD=false
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="$PROJECT_DIR/scripts/backups"
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
DATE_HUMAN=$(date +'%Y-%m-%d %H:%M:%S')

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
log()  { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# --- Parseo de argumentos --------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep) KEEP="$2"; shift 2 ;;
        --upload) UPLOAD=true; shift ;;
        -h|--help)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *) fail "Argumento desconocido: $1" ;;
    esac
done

# --- Validaciones --------------------------------------------------------
command -v docker >/dev/null 2>&1 || fail "Docker no esta instalado"
command -v mysqldump >/dev/null 2>&1 || warn "mysqldump no esta en el host; intentare usar el del contenedor"

cd "$PROJECT_DIR"
mkdir -p "$BACKUP_ROOT/db" "$BACKUP_ROOT/chroma"

# Verificar que la pila este corriendo
if ! docker compose ps db_relacional 2>/dev/null | grep -q "Up\|healthy"; then
    fail "El servicio db_relacional no esta corriendo. Ejecuta: docker compose up -d"
fi

# --- 1. Backup de MySQL ----------------------------------------------------
DB_BACKUP="$BACKUP_ROOT/db/${TIMESTAMP}.sql"
log "Exportando base de datos MySQL..."

# Tomar credenciales del .env
source .env
MYSQL_PASS="${MYSQL_ROOT_PASSWORD:-demo}"
MYSQL_DB="${MYSQL_DATABASE:-its_murialdo}"

# Usar mysqldump dentro del contenedor para no requerir cliente en el host
docker compose exec -T db_relacional \
    mysqldump -u root -p"${MYSQL_PASS}" \
    --single-transaction --quick --routines --triggers \
    --databases "${MYSQL_DB}" \
    > "$DB_BACKUP"

DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
log "Dump SQL guardado: $DB_BACKUP ($DB_SIZE)"

# --- 2. Backup de ChromaDB -------------------------------------------------
CHROMA_BACKUP="$BACKUP_ROOT/chroma/${TIMESTAMP}.tar.gz"
log "Empaquetando volumen ChromaDB..."

# Forzar un flush al disco antes de empaquetar
docker compose exec -T app_tutor \
    sh -c "sync && echo 3 > /proc/sys/vm/drop_caches" 2>/dev/null || true

# Detener temporalmente el contenedor para evitar inconsistencias
# (alternativa: hacer backup en caliente, valido para ChromaDB)
docker compose stop app_tutor

# Empaquetar el volumen
VOLUME_NAME=$(docker volume inspect --format '{{.Name}}' its_rag_math_chroma_data 2>/dev/null || echo "")
if [ -z "$VOLUME_NAME" ]; then
    # Fallback: buscar por nombre
    VOLUME_NAME=$(docker volume ls --format '{{.Name}}' | grep -E "chroma" | head -1)
fi

if [ -n "$VOLUME_NAME" ]; then
    docker run --rm \
        -v "${VOLUME_NAME}:/data:ro" \
        -v "$BACKUP_ROOT/chroma:/backup" \
        alpine tar czf "/backup/${TIMESTAMP}.tar.gz" -C /data .
    CHROMA_SIZE=$(du -h "$CHROMA_BACKUP" | cut -f1)
    log "ChromaDB guardado: $CHROMA_BACKUP ($CHROMA_SIZE)"
else
    warn "No se encontro el volumen de ChromaDB. Backup omitido."
    CHROMA_BACKUP=""
fi

# Reiniciar app_tutor
docker compose start app_tutor

# --- 3. Metadatos del backup ----------------------------------------------
MANIFEST="$BACKUP_ROOT/db/${TIMESTAMP}.json"
cat > "$MANIFEST" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "date_human": "$DATE_HUMAN",
  "project": "its_rag_math",
  "db_backup": "$DB_BACKUP",
  "db_size": "$DB_SIZE",
  "chroma_backup": "$CHROMA_BACKUP",
  "chroma_size": "${CHROMA_SIZE:-N/A}",
  "mysql_version": "$(docker compose exec -T db_relacional mysql --version 2>/dev/null | head -1 || echo 'unknown')",
  "retention_keep": $KEEP
}
EOF

log "Manifest guardado: $MANIFEST"

# --- 4. Rotacion de backups antiguos --------------------------------------
log "Aplicando retencion (mantener ultimos $KEEP backups)..."

# Borrar dumps SQL antiguos
find "$BACKUP_ROOT/db" -name "*.sql" -type f -mtime +$KEEP -delete 2>/dev/null || true
# Borrar tar.gz antiguos
find "$BACKUP_ROOT/chroma" -name "*.tar.gz" -type f -mtime +$KEEP -delete 2>/dev/null || true
# Borrar manifests antiguos
find "$BACKUP_ROOT/db" -name "*.json" -type f -mtime +$KEEP -delete 2>/dev/null || true

TOTAL_DB=$(ls -1 "$BACKUP_ROOT/db"/*.sql 2>/dev/null | wc -l)
TOTAL_CHROMA=$(ls -1 "$BACKUP_ROOT/chroma"/*.tar.gz 2>/dev/null | wc -l)
log "Backups restantes: $TOTAL_DB SQL, $TOTAL_CHROMA ChromaDB"

# --- 5. Upload remoto (opcional) -----------------------------------------
if [ "$UPLOAD" = true ]; then
    log "Subiendo backups a almacenamiento remoto..."

    # ============================================================
    # CONFIGURAR AQUI: descomenta UNA de las siguientes opciones
    # ============================================================

    # Opcion A: AWS S3 (requiere awscli configurado)
    # if command -v aws >/dev/null 2>&1; then
    #     aws s3 cp "$DB_BACKUP" "s3://tu-bucket-its/backups/db/${TIMESTAMP}.sql"
    #     [ -n "$CHROMA_BACKUP" ] && aws s3 cp "$CHROMA_BACKUP" "s3://tu-bucket-its/backups/chroma/${TIMESTAMP}.tar.gz"
    #     log "Subido a S3."
    # fi

    # Opcion B: Backblaze B2 (requiere b2 CLI configurado)
    # if command -v b2 >/dev/null 2>&1; then
    #     b2 upload-file "$DB_BACKUP" "tu-bucket/db/${TIMESTAMP}.sql"
    #     [ -n "$CHROMA_BACKUP" ] && b2 upload-file "$CHROMA_BACKUP" "tu-bucket/chroma/${TIMESTAMP}.tar.gz"
    #     log "Subido a B2."
    # fi

    # Opcion C: rsync a otro servidor
    # rsync -avz "$BACKUP_ROOT/" backup-user@backup-server:/backups/its_rag_math/

    warn "Upload remoto no configurado. Edita scripts/backup.sh para activarlo."
fi

log "===== BACKUP COMPLETADO ====="
log "SQL:  $DB_BACKUP"
log "Chroma: $CHROMA_BACKUP"
log "Manifest: $MANIFEST"
