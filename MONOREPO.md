# Monorepo - Blockchain Centralizada

Este proyecto es un monorepo que combina:
- **Backend**: Python (FastAPI) - API REST para la blockchain
- **Frontend**: Next.js (React) - Interfaz web del explorador

## Estructura del Proyecto

```
blockchain-centralizada/
├── src/              # Backend Python (FastAPI)
├── frontend/         # Frontend Next.js
├── static/           # Archivos estáticos legacy (explorer.html)
├── docker-compose.yml
└── Dockerfile        # Construye backend + frontend
```

## Desarrollo Local

### Backend (Python)
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python src/main.py
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

El frontend se ejecutará en http://localhost:3000

## Construcción para Producción

### Opción 1: Construir todo con Docker
```bash
docker-compose build blockchain
docker-compose up -d blockchain
```

El Dockerfile construye automáticamente el frontend Next.js y lo sirve desde FastAPI en el puerto 8000.

### Opción 2: Construir frontend manualmente
```bash
cd frontend
npm install
npm run build
```

Los archivos estáticos se generarán en `frontend/out/` y FastAPI los servirá automáticamente.

## Acceso

- **Frontend Next.js**: http://localhost:8000/
- **API Backend**: http://localhost:8000/api/ (o directamente http://localhost:8000/chain, etc.)
- **Explorador Legacy**: http://localhost:8000/explorer
- **Documentación API**: http://localhost:8000/docs

## Características

- ✅ Monorepo con Python + Next.js
- ✅ Todo servido desde el mismo puerto (8000)
- ✅ Sin necesidad de nginx
- ✅ Frontend construido como estático y servido por FastAPI
- ✅ Desarrollo independiente del frontend (puerto 3000) y backend (puerto 8000)

## Notas

- El frontend Next.js se construye como estático (`output: 'export'`)
- FastAPI sirve los archivos estáticos desde `frontend/out/`
- Las rutas del frontend se manejan con SPA routing (todas las rutas sirven `index.html`)

