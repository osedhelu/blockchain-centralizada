# Frontend - Blockchain Explorer

Frontend construido con Next.js para el explorador de blockchain.

## Desarrollo

```bash
cd frontend
npm install
npm run dev
```

El frontend se ejecutará en http://localhost:3000

## Construcción para Producción

```bash
cd frontend
npm install
npm run build
```

Los archivos estáticos se generarán en `frontend/out/` y serán servidos por FastAPI en el puerto 8000.

## Estructura

- `app/` - Aplicación Next.js con App Router
- `app/page.tsx` - Página principal
- `app/components/` - Componentes React
  - `Explorer.tsx` - Explorador de blockchain
  - `Wallet.tsx` - Gestión de wallets
  - `Blocks.tsx` - Visualización de bloques
  - `MetaMask.tsx` - Integración con MetaMask

