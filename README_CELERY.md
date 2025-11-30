# Celery - Sistema de Tareas Asíncronas

El sistema utiliza Celery para el procesamiento asíncrono de tareas, mejorando el rendimiento y la escalabilidad de la blockchain.

## Arquitectura

- **RabbitMQ**: Broker de mensajes (cola de tareas)
- **Redis**: Backend de resultados (almacena resultados de tareas)
- **Celery Workers**: Procesan las tareas de forma asíncrona
- **Flower**: Interfaz web para monitorear Celery

## Servicios Celery

### 1. Celery Worker

Procesa las tareas asíncronas en diferentes colas:
- `default`: Tareas generales
- `mining`: Tareas de minería de bloques
- `transactions`: Procesamiento de transacciones
- `validation`: Validación de la cadena
- `cache`: Actualización de caché

### 2. Flower (Monitoreo)

Interfaz web para monitorear Celery:
- URL: `http://localhost:5555`
- Ver estado de tareas en tiempo real
- Monitorear workers y colas
- Ver historial de tareas

## Tareas Disponibles

### Minería de Bloques

```bash
# Modo asíncrono (recomendado)
curl -X POST http://localhost:8000/mine?async_mode=true \
  -H "Content-Type: application/json" \
  -d '{"mining_reward_address": "0xTuDireccion"}'

# Modo síncrono
curl -X POST http://localhost:8000/mine?async_mode=false \
  -H "Content-Type: application/json" \
  -d '{"mining_reward_address": "0xTuDireccion"}'
```

### Procesamiento de Transacciones

```bash
# Modo asíncrono
curl -X POST "http://localhost:8000/transactions/new?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "0xAlice",
    "recipient": "0xBob",
    "amount": 100.5
  }'

# Modo síncrono
curl -X POST "http://localhost:8000/transactions/new?async_mode=false" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "0xAlice",
    "recipient": "0xBob",
    "amount": 100.5
  }'
```

### Procesamiento en Lote

```bash
curl -X POST http://localhost:8000/transactions/batch \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {"sender": "0xAlice", "recipient": "0xBob", "amount": "100"},
      {"sender": "0xBob", "recipient": "0xCharlie", "amount": "50"}
    ]
  }'
```

### Validación Asíncrona

```bash
curl -X POST http://localhost:8000/tasks/validate-chain
```

### Actualización de Caché

```bash
curl -X POST http://localhost:8000/tasks/update-cache
```

## Monitoreo de Tareas

### Ver Estado de una Tarea

```bash
curl http://localhost:8000/tasks/{task_id}
```

Ejemplo de respuesta:
```json
{
  "task_id": "abc123...",
  "state": "SUCCESS",
  "status": "Tarea completada exitosamente",
  "result": {
    "success": true,
    "message": "Bloque minado exitosamente",
    "block": {...}
  }
}
```

### Estados de Tareas

- **PENDING**: La tarea está esperando ser procesada
- **PROGRESS**: La tarea está en progreso
- **SUCCESS**: Tarea completada exitosamente
- **FAILURE**: La tarea falló
- **REVOKED**: La tarea fue cancelada

## Flower - Interfaz Web

Accede a Flower en: `http://localhost:5555`

Características:
- Ver todas las tareas en tiempo real
- Monitorear workers activos
- Ver estadísticas de rendimiento
- Revisar historial de tareas
- Cancelar tareas si es necesario

## Configuración

### Variables de Entorno

```env
# Celery Configuration
FLOWER_PORT=5555
```

### Colas de Tareas

Las tareas se distribuyen automáticamente en diferentes colas:

- **mining**: Minería de bloques (puede tardar mucho tiempo)
- **transactions**: Procesamiento de transacciones (rápido)
- **validation**: Validación de cadena (medio)
- **cache**: Actualización de caché (rápido)
- **default**: Otras tareas

## Ventajas del Modo Asíncrono

1. **No bloquea la API**: Las peticiones responden inmediatamente
2. **Mejor rendimiento**: Las tareas pesadas no bloquean el servidor
3. **Escalabilidad**: Puedes agregar más workers según necesidad
4. **Monitoreo**: Puedes ver el progreso de las tareas
5. **Resiliencia**: Las tareas se reintentan automáticamente si fallan

## Ejemplo de Flujo Completo

```bash
# 1. Crear transacción (asíncrona)
RESPONSE=$(curl -X POST "http://localhost:8000/transactions/new?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{"sender": "0xAlice", "recipient": "0xBob", "amount": 100}')

TASK_ID=$(echo $RESPONSE | jq -r '.task_id')

# 2. Verificar estado de la tarea
curl http://localhost:8000/tasks/$TASK_ID

# 3. Minar bloque (asíncrono)
RESPONSE=$(curl -X POST "http://localhost:8000/mine?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{"mining_reward_address": "0xMiner"}')

TASK_ID=$(echo $RESPONSE | jq -r '.task_id')

# 4. Esperar y verificar resultado
sleep 5
curl http://localhost:8000/tasks/$TASK_ID
```

## Solución de Problemas

### El worker no procesa tareas

1. Verifica que el worker esté corriendo:
```bash
docker-compose ps celery_worker
```

2. Verifica los logs:
```bash
docker-compose logs celery_worker
```

3. Verifica la conexión a RabbitMQ y Redis

### Las tareas fallan

1. Revisa los logs del worker
2. Verifica el estado en Flower: `http://localhost:5555`
3. Revisa los errores en el endpoint `/tasks/{task_id}`

### Aumentar Workers

Puedes escalar los workers editando `docker-compose.yml`:

```yaml
celery_worker:
  # ... configuración ...
  command: celery -A src.celery_app worker --loglevel=info --concurrency=8
```

O ejecutar múltiples instancias:
```bash
docker-compose up -d --scale celery_worker=3
```

