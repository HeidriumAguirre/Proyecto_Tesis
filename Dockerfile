FROM python:3.11-slim

WORKDIR /app

# Instalamos uv para mantener la velocidad de dependencias que ya usas
RUN pip install uv

# Copiamos los archivos de dependencias
COPY pyproject.tomluv.lock ./

# Instalamos las librerías en el contenedor de forma limpia
RUN uv pip install --system -r pyproject.toml

# Copiamos el resto del código
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]