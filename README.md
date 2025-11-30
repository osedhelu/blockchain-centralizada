# Blockchain Centralizada

Sistema de blockchain centralizada desarrollado en Python que utiliza PostgreSQL para almacenamiento persistente, Redis para caché y RabbitMQ para comunicación entre servicios.

## Arquitectura

- **PostgreSQL**: Almacena los bloques y transacciones de forma persistente
- **Redis**: Caché para estado de la blockchain y transacciones pendientes
- **RabbitMQ**: Sistema de mensajería para comunicación entre servicios
- **FastAPI**: API REST para interactuar con la blockchain
- **Wallets Ethereum**: Sistema de wallets con mnemonic de 12 palabras (BIP39/BIP44)
- **Explorador Web**: Interfaz web estilo Binance para explorar la blockchain

## Requisitos Previos

- Docker y Docker Compose instalados
- Python 3.11+ (solo si ejecutas localmente sin Docker)

## Instalación y Despliegue Rápido

### 1. Configurar Variables de Entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

### 2. Editar el archivo `.env`

Abre el archivo `.env` y configura las siguientes variables según tus necesidades:

```env
# PostgreSQL Configuration
POSTGRES_DB=blockchain_db
POSTGRES_USER=blockchain_user
POSTGRES_PASSWORD=TU_CONTRASEÑA_SEGURA_AQUI
POSTGRES_PORT=5432

# Redis Configuration
REDIS_PASSWORD=TU_CONTRASEÑA_REDIS_AQUI
REDIS_PORT=6379

# RabbitMQ Configuration
RABBITMQ_USER=rabbitmq_user
RABBITMQ_PASSWORD=TU_CONTRASEÑA_RABBITMQ_AQUI
RABBITMQ_PORT=5672
RABBITMQ_MANAGEMENT_PORT=15672

# Blockchain Configuration
BLOCKCHAIN_DIFFICULTY=4
BLOCKCHAIN_MINING_REWARD=100
BLOCKCHAIN_API_PORT=8000

# Application Configuration
LOG_LEVEL=INFO
```

**IMPORTANTE**: Cambia todas las contraseñas por valores seguros antes de desplegar en producción.

### 3. Iniciar los Servicios

```bash
docker-compose up -d
```

Este comando iniciará todos los servicios:
- PostgreSQL en el puerto 5432
- Redis en el puerto 6379
- RabbitMQ en los puertos 5672 (AMQP) y 15672 (Management UI)
- Servicio Blockchain API en el puerto 8000

### 4. Verificar que los Servicios Estén Funcionando

```bash
docker-compose ps
```

Todos los servicios deben estar en estado "Up".

### 5. Acceder a la API y Explorador

- **API**: `http://localhost:8000`
- **Explorador Web**: `http://localhost:8000/explorer`
- **Documentación API**:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

### 6. Acceder a RabbitMQ Management

- URL: `http://localhost:15672`
- Usuario: El valor de `RABBITMQ_USER` en tu `.env`
- Contraseña: El valor de `RABBITMQ_PASSWORD` en tu `.env`

## Uso de la API

### Obtener información de la cadena

```bash
curl http://localhost:8000/chain/info
```

### Crear una transacción

```bash
curl -X POST http://localhost:8000/transactions/new \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Alice",
    "recipient": "Bob",
    "amount": 50.0
  }'
```

### Ver transacciones pendientes

```bash
curl http://localhost:8000/transactions/pending
```

### Minar un bloque

```bash
curl -X POST http://localhost:8000/mine \
  -H "Content-Type: application/json" \
  -d '{
    "mining_reward_address": "Miner1"
  }'
```

### Obtener balance de una dirección

```bash
curl http://localhost:8000/balance/Alice
```

### Obtener toda la cadena

```bash
curl http://localhost:8000/chain
```

### Validar la cadena

```bash
curl http://localhost:8000/chain/validate
```

## Sistema de Wallets

### Generar Wallet desde Línea de Comandos

El proyecto incluye scripts para generar wallets Ethereum con mnemonic de 12 palabras:

```bash
# Generar nueva wallet (posición 0)
python generate_wallet.py

# Generar wallet en posición 1 (método 1)
python generate_wallet.py --index 1

# Generar wallet en posición 1 (método 2 - script específico)
python scripts/generate_wallet_position1.py

# Importar wallet desde mnemonic existente
python generate_wallet.py --mnemonic "palabra1 palabra2 ... palabra12" --index 0

# Formato JSON
python generate_wallet.py --format json --index 1
```

**Nota**: Para generar wallets en posiciones diferentes a 0, necesitas tener instalada la librería `hdwallet`:
```bash
pip install hdwallet
```

### Endpoints de Wallets

#### Generar nueva wallet

```bash
curl -X POST http://localhost:8000/wallet/generate \
  -H "Content-Type: application/json" \
  -d '{"account_index": 0}'
```

#### Importar wallet desde mnemonic

```bash
curl -X POST http://localhost:8000/wallet/import \
  -H "Content-Type: application/json" \
  -d '{
    "mnemonic": "palabra1 palabra2 ... palabra12",
    "account_index": 0
  }'
```

#### Consultar balance de wallet

```bash
curl http://localhost:8000/wallet/0xTuDireccion/balance
```

#### Obtener transacciones de una wallet

```bash
curl http://localhost:8000/wallet/0xTuDireccion/transactions
```

## Explorador Web

El explorador web está disponible en `http://localhost:8000/explorer` y permite:

- **Explorador**: Ver estadísticas de la blockchain y buscar direcciones
- **Wallet**: Generar e importar wallets, consultar balances y transacciones
- **Bloques**: Ver todos los bloques de la cadena

### Características del Explorador

- Interfaz estilo Binance con diseño moderno
- Generación de wallets con mnemonic de 12 palabras
- Consulta de balances en tiempo real
- Visualización de transacciones por dirección
- Exploración de bloques y transacciones

## Estructura del Proyecto

```
blockchain-centralizada/
├── docker-compose.yml      # Configuración de servicios Docker
├── Dockerfile              # Imagen Docker para el servicio Python
├── requirements.txt        # Dependencias de Python
├── .env.example           # Plantilla de variables de entorno
├── .env                   # Variables de entorno (no versionado)
├── README.md              # Este archivo
├── generate_wallet.py    # Script para generar wallets desde CLI
├── static/
│   └── explorer.html     # Explorador web estilo Binance
└── src/
    ├── __init__.py
    ├── main.py            # Punto de entrada de la aplicación
    ├── config.py          # Configuración y variables de entorno
    ├── models.py          # Modelos de datos (Block, Transaction, Blockchain)
    ├── database.py        # Cliente de PostgreSQL
    ├── redis_client.py    # Cliente de Redis
    ├── rabbitmq_client.py # Cliente de RabbitMQ
    ├── blockchain_service.py # Lógica de negocio de la blockchain
    ├── wallet.py          # Gestión de wallets Ethereum
    └── api.py             # Endpoints de FastAPI
```

## Detener los Servicios

```bash
docker-compose down
```

Para eliminar también los volúmenes (datos persistentes):

```bash
docker-compose down -v
```

## Desarrollo Local (sin Docker)

Si prefieres ejecutar sin Docker:

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Asegúrate de tener PostgreSQL, Redis y RabbitMQ ejecutándose localmente

3. Configura el archivo `.env` con las credenciales locales

4. Ejecuta la aplicación:
```bash
python src/main.py
```

## Variables de Entorno Importantes

- `BLOCKCHAIN_DIFFICULTY`: Número de ceros al inicio del hash (dificultad de minería)
- `BLOCKCHAIN_MINING_REWARD`: Recompensa por minar un bloque
- `LOG_LEVEL`: Nivel de logging (DEBUG, INFO, WARNING, ERROR)

## Notas

- Los datos se persisten en volúmenes Docker, por lo que sobrevivirán a reinicios
- La blockchain se inicializa automáticamente con un bloque génesis
- Las transacciones se publican en RabbitMQ para procesamiento asíncrono
- Redis se usa para caché de estado y transacciones pendientes

## Solución de Problemas

Si algún servicio no inicia:

1. Verifica los logs:
```bash
docker-compose logs [nombre_servicio]
```

2. Verifica que los puertos no estén en uso

3. Asegúrate de que el archivo `.env` esté correctamente configurado

4. Verifica la conectividad entre servicios:
```bash
docker-compose exec blockchain ping postgres
docker-compose exec blockchain ping redis
docker-compose exec blockchain ping rabbitmq
```

