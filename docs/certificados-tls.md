# Generación de certificados TLS autofirmados para Streamlit

Streamlit requiere HTTPS para que el navegador autorice `getUserMedia()`
(acceso al micrófono). Como el piloto se ejecuta en red local, se usa
un certificado autofirmado generado con `mkcert`.

## 1) Instalar mkcert

Windows (con Chocolatey):
```
choco install mkcert
```

macOS:
```
brew install mkcert
```

Linux (Debian/Ubuntu):
```
sudo apt install mkcert
```

Tras instalar:
```
mkcert -install   # crea la CA local de confianza
```

## 2) Generar el certificado para localhost y 127.0.0.1

Desde la raíz del proyecto:

```bash
mkdir -p docker/certs
mkcert -cert-file docker/certs/server.crt \
       -key-file docker/certs/server.key \
       localhost 127.0.0.1
```

## 3) Verificar que Docker Compose los monte

El servicio `app_tutor` incluye:

```yaml
volumes:
  - ./docker/certs:/app/certs:ro
```

Y Streamlit los carga con:

```
--server.sslCertFile=/app/certs/server.crt
--server.sslKeyFile=/app/certs/server.key
```

## 4) Acceder a la app

```
https://localhost:8501
```

El navegador mostrará una advertencia de cert autofirmado: acéptala
una vez (es la CA local de mkcert).

## Producción

Para un despliegue real (colegio, internet) sustituye estos certs
por uno emitido por Let's Encrypt o el cert institucional del colegio,
montado en el mismo path.
