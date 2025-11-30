# Guía Rápida - Blockchain Centralizada con Wallets

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
cp .env.example .env
# Edita .env y cambia las contraseñas
```

### 2. Iniciar Servicios

```bash
docker-compose up -d
```

### 3. Acceder al Explorador Web

Abre tu navegador en: **http://localhost:8000/explorer**

## 💼 Generar Wallets

### Opción 1: Desde el Explorador Web

1. Ve a la pestaña "Wallet"
2. Click en "Generar Wallet"
3. Guarda el mnemonic de 12 palabras de forma segura

### Opción 2: Desde Línea de Comandos

#### Generar Wallet en Posición 0 (primera wallet)
```bash
python generate_wallet.py
```

#### Generar Wallet en Posición 1 (segunda wallet)
```bash
python generate_wallet.py --index 1
```

O usando el script específico:
```bash
python scripts/generate_wallet_position1.py
```

#### Importar Wallet desde Mnemonic
```bash
python generate_wallet.py --mnemonic "palabra1 palabra2 ... palabra12" --index 0
```

## 🔍 Consultar Saldo de Wallet

### Desde el Explorador Web

1. Ve a la pestaña "Wallet"
2. Ingresa la dirección de la wallet en "Consultar Balance"
3. Click en "Consultar Balance"

### Desde la API

```bash
curl http://localhost:8000/wallet/0xTuDireccion/balance
```

### Desde el Explorador Web - Buscar Dirección

1. Ve a la pestaña "Explorador"
2. Ingresa la dirección en "Buscar Dirección"
3. Verás el balance y todas las transacciones

## 📊 Ver Transacciones de una Wallet

### Desde el Explorador Web

1. Ve a la pestaña "Wallet"
2. Ingresa la dirección en "Transacciones de la Wallet"
3. Click en "Ver Transacciones"

### Desde la API

```bash
curl http://localhost:8000/wallet/0xTuDireccion/transactions
```

## 🎨 Características del Explorador

- **Interfaz estilo Binance**: Diseño moderno y profesional
- **Generación de Wallets**: Crea wallets con mnemonic de 12 palabras
- **Consulta de Balances**: Ver saldos en tiempo real
- **Historial de Transacciones**: Todas las transacciones de una dirección
- **Exploración de Bloques**: Ver todos los bloques de la cadena
- **Estadísticas**: Información general de la blockchain

## 🔐 Seguridad de Wallets

⚠️ **IMPORTANTE**:
- Guarda el mnemonic de 12 palabras en un lugar seguro
- Nunca compartas tu clave privada o mnemonic
- Quien tenga el mnemonic puede controlar todas las wallets derivadas
- Haz copias de seguridad en lugares seguros

## 📝 Estructura de Wallets

Las wallets siguen el estándar BIP44:
- **Posición 0**: `m/44'/60'/0'/0/0`
- **Posición 1**: `m/44'/60'/1'/0/0`
- **Posición N**: `m/44'/60'/{N}'/0/0`

## 🛠️ Solución de Problemas

### Error al generar wallet en posición 1

Instala la librería hdwallet:
```bash
pip install hdwallet
```

O dentro del contenedor Docker:
```bash
docker-compose exec blockchain pip install hdwallet
```

### El explorador no carga

Verifica que el servicio esté corriendo:
```bash
docker-compose ps
```

Verifica los logs:
```bash
docker-compose logs blockchain
```

## 📚 Endpoints de API Disponibles

- `GET /explorer` - Explorador web
- `POST /wallet/generate` - Generar nueva wallet
- `POST /wallet/import` - Importar wallet desde mnemonic
- `GET /wallet/{address}/balance` - Consultar balance
- `GET /wallet/{address}/transactions` - Ver transacciones
- `GET /chain` - Obtener toda la cadena
- `GET /chain/info` - Información de la cadena
- `POST /transactions/new` - Crear transacción
- `POST /mine` - Minar bloque

Para más detalles, visita: http://localhost:8000/docs

