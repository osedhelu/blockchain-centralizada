FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de dependencias
COPY frontend/package*.json ./
RUN npm install

# Copiar código fuente
COPY frontend/ .

# Construir la aplicación
RUN npm run build

# Etapa de producción - solo los archivos estáticos
FROM node:20-alpine

WORKDIR /app

# Copiar solo los archivos construidos
COPY --from=builder /app/out ./out
COPY --from=builder /app/package*.json ./

# Este Dockerfile es solo para construir, los archivos se servirán desde FastAPI
# No necesitamos exponer puertos aquí

