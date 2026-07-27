# Guía de despliegue en VPS

**ITS RAG Math — Colegio Murialdo Valparaíso**

Esta guía describe cómo desplegar el proyecto completo (Streamlit + MySQL + ChromaDB) en un VPS Linux con HTTPS automático vía Let's Encrypt.

---

## Arquitectura desplegada

```
Internet
   │
   │ HTTPS (443) / HTTP (80 → redirige a HTTPS)
   ▼
┌─────────────────────────────┐
│  caddy (contenedor Docker)  │  ← Reverse proxy con Let's Encrypt auto
└──────────────┬──────────────┘
               │ HTTP interno (puerto 8501)
               ▼
┌─────────────────────────────┐
│  app_tutor (Streamlit)      │  ← API + chat + panel docente
└──────────────┬──────────────┘
               │
   ┌───────────┴───────────┐
   ▼                       ▼
┌──────────┐         ┌─────────────────┐
│  MySQL 8 │         │  ChromaDB       │
│ (volumen)│         │  (volumen)      │
└──────────┘         └─────────────────┘
```

**Redes Docker aisladas**:
- `its_net_backend`: red **interna** (sin acceso al host). Conecta MySQL ↔ Streamlit. MySQL nunca es accesible desde Internet.
- `its_net_frontend`: red que conecta Caddy ↔ Streamlit. Caddy es el único expuesto al exterior (puertos 80/443).

---

## Prerrequisitos

### Elegir un proveedor VPS

| Proveedor | Plan mínimo | Costo mensual | Ubicación |
|---|---|---|---|
| **Hetzner** | CX22 (2 vCPU, 4 GB RAM) | ~€4.5 | Europa (Falkenstein, Helsinki) |
| **DigitalOcean** | Basic Droplet (1 vCPU, 1 GB RAM) | $6 | NYC, SFO, AMS, SGP |
| **Vultr** | Cloud Compute (1 vCPU, 1 GB RAM) | $5 | Múltiple |
| **OVH** | Starter (1 vCPU, 2 GB RAM) | €3.5 | Europa |
| **Linode** | Nanode (1 vCPU, 1 GB RAM) | $5 | Múltiple |

**Recomendación**: Hetzner CX22 (€4.5/mes) o DigitalOcean Basic ($6/mes). Suficiente para el piloto de 4 usuarios.

### Requisitos del VPS

- **OS**: Ubuntu 22.04 LTS o Debian 12 (recomendado)
- **RAM mínimo**: 2 GB (recomendado 4 GB)
- **Disco**: 20 GB mínimo
- **Acceso root** durante la instalación
- **Dominio propio** apuntando a la IP pública del VPS (ej: `its.murialdo.example.cl`)

---

## Paso 1: Preparar el VPS (10 min)

Conéctate al VPS como root:

```bash
ssh root@IP-DEL-VPS
```

Instala el script de hardening:

```bash
# Clonar el repo (o copiar los scripts manualmente)
git clone https://github.com/HeidriumAguirre/Proyecto_Tesis.git /opt/its_rag_math
cd /opt/its_rag_math

# Ejecutar el setup base
sudo bash scripts/setup-vps.sh
```

Esto:
- Actualiza el sistema
- Instala Docker + Docker Compose v2
- Configura firewall (UFW) abriendo solo 22, 80, 443
- Activa fail2ban
- Refuerza SSH (deshabilita root login, password auth)
- Configura actualizaciones automáticas
- Crea usuario `deploy` con acceso a Docker

Al finalizar, **cierra sesión como root y vuelve a entrar como `deploy`**:

```bash
exit
ssh deploy@IP-DEL-VPS
```

⚠️ **Antes de desconectar root**, asegúrate de haber agregado tu clave SSH pública a `/home/deploy/.ssh/authorized_keys` (sino te quedas fuera del VPS).

---

## Paso 2: Configurar el DNS (5 min)

En tu proveedor de DNS (Cloudflare, Route53, NIC Chile, etc.), crea un registro:

| Tipo | Nombre | Valor |
|---|---|---|
| A | `its.murialdo.example.cl` | `IP-PUBLICA-DEL-VPS` |

Espera 5-30 minutos a que propague.

Verifica con:

```bash
dig its.murialdo.example.cl
# o
nslookup its.murialdo.example.cl
```

---

## Paso 3: Clonar y configurar el proyecto (5 min)

```bash
cd /opt
sudo git clone https://github.com/HeidriumAguirre/Proyecto_Tesis.git its_rag_math
sudo chown -R deploy:deploy its_rag_math
cd its_rag_math

# Crear .env desde la plantilla
cp .env.production.example .env
nano .env   # editar las 3 variables criticas
```

### Variables que debes rellenar en `.env`

```bash
# Contraseña de MySQL (root) - usa una FUERTE, ej: openssl rand -base64 24
MYSQL_ROOT_PASSWORD=TuPasswordFuerteAqui

# API Key de Gemini - obtener en https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSy...

# Dominio publico (debe coincidir con el DNS)
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

**Genera la contraseña MySQL con**:

```bash
openssl rand -base64 24
```

---

## Paso 4: Configurar el Caddyfile (2 min)

Edita `Caddyfile`:

```bash
nano Caddyfile
```

**Reemplaza**:
- `DOMINIO.example.cl` → tu dominio real (ej: `its.murialdo.example.cl`)
- `TU-EMAIL@example.cl` → tu email (para notificaciones de Let's Encrypt)

Por ejemplo:

```
its.murialdo.example.cl {
    encode zstd gzip
    reverse_proxy app_tutor:8501 { ... }
    email heidrium.aguirre@gmail.com
}
```

---

## Paso 5: Levantar la pila (5 min)

```bash
# Como deploy (miembro del grupo docker)
cd /opt/its_rag_math
bash scripts/deploy.sh
```

El script:
1. Hace `git pull` para asegurar la última versión
2. Verifica que `.env` esté configurado
3. Construye la imagen de `app_tutor`
4. Levanta los 3 servicios (db_relacional, app_tutor, caddy)
5. Espera a que MySQL esté healthy
6. Espera a que Caddy obtenga el certificado HTTPS

Si todo va bien, verás al final:

```
===== URLS DISPONIBLES =====
HTTPS: https://its.murialdo.example.cl
HTTP (redirige a HTTPS): http://its.murialdo.example.cl

===== PROXIMOS PASOS =====
1. Verifica que https://its.murialdo.example.cl carga la app
2. Ingresa con las credenciales seed: ...
```

---

## Paso 6: Verificar (5 min)

Abre en el navegador:

```
https://its.murialdo.example.cl
```

Deberías ver:
- ✅ Candado verde (cert válido de Let's Encrypt)
- ✅ La pantalla de login de Streamlit
- ✅ Redirección automática de HTTP → HTTPS

Prueba el login:
- **Docente**: `heidrium.aguirre@murialdo.cl` / `Demo2026!`
- **Estudiante**: `mateo.gonzalez@murialdo.cl` (sin contraseña)

---

## Paso 7: Backup automático (10 min)

Configura el cron para que ejecute el backup cada noche a las 3 AM:

```bash
# Como deploy
crontab -e
```

Agrega esta línea:

```
0 3 * * * /opt/its_rag_math/scripts/backup.sh >> /var/log/its_backup.log 2>&1
```

Los backups se guardan en `/opt/its_rag_math/scripts/backups/`:

```
backups/
├── db/
│   ├── 20260726_030000.sql
│   ├── 20260726_030000.json
│   └── ...
└── chroma/
    ├── 20260726_030000.tar.gz
    └── ...
```

**Retención por defecto**: 7 días. Edita `--keep 30` en el cron para conservar más.

### Subir backups a S3/B2 (opcional)

Edita `scripts/backup.sh`, descomenta la sección de upload (líneas con `aws s3` o `b2`), configura tus credenciales y reinicia el cron.

---

## Paso 8: Monitoreo y mantenimiento (5 min)

### Comandos útiles

```bash
# Ver logs en vivo
cd /opt/its_rag_math
docker compose logs -f

# Ver logs solo de la app
docker compose logs -f app_tutor

# Ver estado de los servicios
docker compose ps

# Ver uso de recursos
docker stats

# Reiniciar un servicio especifico
docker compose restart app_tutor

# Actualizar el codigo (despues de git push)
git pull
docker compose up -d --build app_tutor
```

### Health check externo (opcional)

Configura un servicio como [UptimeRobot](https://uptimerobot.com) (gratis) o [BetterStack](https://betterstack.com) para monitorear `https://its.murialdo.example.cl` cada 5 minutos y recibir alertas por email/Slack si la app cae.

---

## Paso 9: Renovar el certificado SSL

**No tienes que hacer nada**. Caddy + Let's Encrypt renuevan automáticamente el certificado cuando faltan menos de 30 días para expirar (cada 60 días aprox).

Si quieres forzar la renovación:

```bash
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

---

## Troubleshooting

### La app no arranca

```bash
docker compose logs app_tutor | tail -100
docker compose logs db_relacional | tail -50
```

### Caddy no obtiene certificado HTTPS

```bash
docker compose logs caddy | tail -50
```

Verifica que:
- El DNS del dominio apunta a la IP del VPS
- Los puertos 80 y 443 están abiertos: `sudo ufw status`
- No hay otro servicio usando los puertos 80/443

### MySQL no arranca

```bash
docker compose logs db_relacional | tail -50
```

Verifica que la contraseña en `.env` no tenga caracteres especiales que rompan el YAML. Si tiene `$`, `&`, `#`, usa comillas en el `.env`.

### Restablecer todo desde cero (último recurso)

```bash
cd /opt/its_rag_math
docker compose down -v   # ⚠️ BORRA LOS VOLUMENES (datos)
bash scripts/deploy.sh
docker compose exec app_tutor python database/seed.py
```

---

## Costos estimados

| Concepto | Costo |
|---|---|
| VPS Hetzner CX22 | €4.5/mes |
| Dominio (.cl) | ~$10 USD/año (NIC Chile) |
| Let's Encrypt SSL | Gratis |
| GitHub repo (privado) | Gratis (con student pack) o $4/mes |
| Backups locales en VPS | Incluidos en el disco |
| **Total mensual** | **~€5/mes** (~CLP $5.000) |

---

## Resumen de archivos de despliegue

| Archivo | Propósito |
|---|---|
| `docker-compose.yml` | 3 servicios: `db_relacional`, `app_tutor`, `caddy` con redes aisladas |
| `Caddyfile` | Reverse proxy con HTTPS automático y headers de seguridad |
| `.env.production.example` | Plantilla de variables para producción |
| `scripts/setup-vps.sh` | Hardening inicial del VPS (Docker, UFW, fail2ban, SSH) |
| `scripts/deploy.sh` | Despliegue + verificación de la pila |
| `scripts/backup.sh` | Backup automático de MySQL + ChromaDB |
| `docs/DEPLOY_VPS.md` | Este documento |

---

## Próximos pasos (post-piloto)

- Configurar monitoreo externo (UptimeRobot, Grafana, etc.)
- Configurar alertas por Slack/email
- Evaluar migrar a Kubernetes si el piloto crece
- Considerar Hetzner Storage Box para backups off-site
- Internacionalización (es-CL ya es nativo; soporte en-US si se requiere)
