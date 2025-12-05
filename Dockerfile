FROM python:3.11-slim

# diretório de trabalho
WORKDIR /app

# instalar dependências de sistema necessárias para wheels/compilação
# reduzir tamanho com --no-install-recommends
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libatlas-base-dev \
    libopenblas-dev \
    liblapack-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# copiar requirements e atualizar pip/setuptools/wheel
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
# instalar apenas runtime deps; se tiver dev deps, mova para requirements-dev.txt
RUN pip install --no-cache-dir -r requirements.txt

# copiar código
COPY . .

ENV SWISS_EPHE_PATH=/app/ephe

# porta e comando
CMD ["streamlit","run","app.py","--server.port=8501","--server.headless=true"]

LABEL org.opencontainers.image.title="Etheria"
LABEL org.opencontainers.image.description="Painel esotérico — numerologia, arcanos e ciclos"