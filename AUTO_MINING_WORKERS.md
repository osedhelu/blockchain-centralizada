# 🤖 Workers de Minado Automático

## Configuración

Se han creado **3 workers de Celery** que minan automáticamente las transacciones pendientes **sin pagar comisiones**.

## Características

- ✅ **3 Workers independientes**: `celery_worker_1`, `celery_worker_2`, `celery_worker_3`
- ✅ **Minado automático**: Cada 30 segundos verifican si hay transacciones pendientes
- ✅ **Sin recompensa**: Los workers minan sin recibir tokens de recompensa
- ✅ **Distribución de carga**: Los 3 workers comparten el trabajo
- ✅ **Celery Beat**: Programa las tareas automáticas cada 30 segundos

## Cómo Funciona

1. **Celery Beat** programa la tarea `auto_mine_task` cada 30 segundos
2. La tarea se envía a la cola `auto_mining`
3. Uno de los 3 workers toma la tarea
4. El worker verifica si hay transacciones pendientes
5. Si hay transacciones, mina el bloque **sin agregar recompensa**
6. Las transacciones se confirman automáticamente

## Iniciar los Workers

```bash
# Iniciar todos los servicios (incluyendo los 3 workers)
docker-compose up -d

# Ver logs de los workers
docker-compose logs -f celery_worker_1
docker-compose logs -f celery_worker_2
docker-compose logs -f celery_worker_3

# Ver logs de Celery Beat (programador de tareas)
docker-compose logs -f celery_beat
```

## Verificar que Están Funcionando

```bash
# Ver estado de los contenedores
docker-compose ps

# Ver logs combinados de todos los workers
docker-compose logs celery_worker_1 celery_worker_2 celery_worker_3

# Verificar que están minando
docker-compose logs celery_worker_1 | grep "minando\|Bloque"
```

## Configuración de Intervalo

Para cambiar la frecuencia del minado automático, edita `src/celery_app.py`:

```python
beat_schedule={
    'auto-mine-every-30-seconds': {
        'task': 'src.tasks.auto_mine_task',
        'schedule': 30.0,  # Cambia este valor (en segundos)
    },
},
```

Ejemplos:
- `10.0` = cada 10 segundos
- `60.0` = cada 60 segundos (1 minuto)
- `300.0` = cada 5 minutos

## Diferencias entre Minado Manual y Automático

### Minado Manual (desde el frontend/API)
- Puedes especificar una dirección para recibir recompensa
- Recibes tokens por minar
- Debes hacer clic en "Minar Bloque"

### Minado Automático (workers)
- No hay recompensa (minan gratis)
- Se ejecuta automáticamente cada 30 segundos
- Confirma transacciones pendientes sin intervención

## Monitoreo

Puedes monitorear los workers usando Flower:

```bash
# Acceder a Flower (si está configurado)
http://localhost:5555
```

O ver los logs directamente:

```bash
# Ver logs en tiempo real
docker-compose logs -f celery_worker_1 celery_worker_2 celery_worker_3 celery_beat
```

## Troubleshooting

### Los workers no están minando

1. Verifica que Celery Beat esté corriendo:
   ```bash
   docker-compose ps celery_beat
   ```

2. Verifica los logs:
   ```bash
   docker-compose logs celery_beat
   ```

3. Verifica que haya transacciones pendientes:
   ```bash
   curl http://localhost:8000/transactions/pending
   ```

### Los workers están minando pero con recompensa

Verifica que el código esté actualizado y que los workers estén usando la versión correcta:
```bash
docker-compose restart celery_worker_1 celery_worker_2 celery_worker_3 celery_beat
```

## Resumen

- **3 Workers** minando automáticamente
- **Sin recompensa** (gratis)
- **Cada 30 segundos** verifican transacciones pendientes
- **Confirman automáticamente** todas las transacciones pendientes

¡Las transacciones ahora se confirmarán automáticamente sin necesidad de minar manualmente! 🎉

