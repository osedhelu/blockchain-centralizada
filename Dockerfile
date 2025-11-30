FROM python:3.11-slim

WORKDIR /app

# Instalar Node.js para construir el frontend
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Construir frontend Next.js
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ .
RUN npm run build

# Volver al directorio de trabajo principal
WORKDIR /app

# Copiar código fuente Python
COPY src/ ./src/
COPY static/ ./static/

ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]

