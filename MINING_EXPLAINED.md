# 🔨 Guía Completa del Minado en la Blockchain

## ¿Qué es el Minado?

El **minado** es el proceso de confirmar y agregar transacciones pendientes a la blockchain creando un nuevo bloque. Es como "sellar" un grupo de transacciones para que sean válidas y permanentes.

## ¿Por qué es Necesario?

1. **Confirmar Transacciones**: Las transacciones que creas quedan "pendientes" hasta que se minan
2. **Actualizar Balances**: Los balances solo cambian cuando las transacciones están en un bloque minado
3. **Seguridad**: El proceso de minado asegura que las transacciones sean válidas y no se puedan modificar

## ¿Cómo Funciona Técnicamente?

### 1. **Proof of Work (Prueba de Trabajo)**

El minado usa un algoritmo llamado **Proof of Work** que requiere resolver un problema matemático:

```python
# El algoritmo busca un hash que empiece con cierta cantidad de ceros
target = "0" * difficulty  # Ejemplo: "0000" si difficulty = 4
while hash[:difficulty] != target:
    nonce += 1  # Incrementa un número aleatorio
    hash = calcular_hash(bloque + nonce)  # Calcula nuevo hash
```

### 2. **Parámetros Importantes**

- **Difficulty (Dificultad)**: Por defecto es `4`, significa que el hash debe empezar con 4 ceros (`0000...`)
  - Más dificultad = más tiempo de minado = más seguridad
  - Menos dificultad = menos tiempo = menos seguridad
  
- **Nonce**: Un número que se incrementa hasta encontrar el hash correcto
  - Es como "adivinar" el número correcto
  - Puede tomar desde segundos hasta minutos dependiendo de la dificultad

- **Mining Reward (Recompensa)**: Por defecto es `100` tokens
  - Se otorga automáticamente al minero que crea el bloque
  - Es una transacción especial del "Sistema" a tu dirección

### 3. **Proceso Paso a Paso**

```
1. Tienes transacciones pendientes
   ↓
2. Creas un bloque con esas transacciones
   ↓
3. Agregas una transacción de recompensa para ti
   ↓
4. Empiezas a buscar el hash correcto (minar)
   - Incrementas el nonce
   - Calculas el hash
   - ¿Empieza con "0000"? → NO → Repite
   - ¿Empieza con "0000"? → SÍ → ¡Bloque minado!
   ↓
5. Guardas el bloque en la base de datos
   ↓
6. Las transacciones pendientes se confirman
   ↓
7. Los balances se actualizan
   ↓
8. Recibes tu recompensa de minería
```

## ¿Qué Tienes que Hacer?

### Opción 1: Desde el Frontend (Más Fácil)

1. **Ve a la pestaña "Explorador"**
2. **Desplázate hasta "Minar Bloque"**
3. **Ingresa tu dirección** (la que recibirá la recompensa de 100 tokens)
4. **Haz clic en "Minar Bloque"**
5. **Espera** a que termine (puede tomar unos segundos o minutos)
6. **¡Listo!** Las transacciones están confirmadas y recibiste tu recompensa

### Opción 2: Desde la API (Para Desarrolladores)

```bash
# Minar un bloque
curl -X POST http://localhost:8000/mine \
  -H "Content-Type: application/json" \
  -d '{"mining_reward_address": "0xTuDireccion"}'
```

## Ejemplo Visual

### Antes de Minar:
```
Transacciones Pendientes:
- TX1: 0xAAA → 0xBBB (100 tokens)
- TX2: 0xCCC → 0xDDD (50 tokens)

Balances:
- 0xAAA: 1000 tokens (no cambió aún)
- 0xBBB: 500 tokens (no cambió aún)
```

### Después de Minar:
```
Bloque #1 Minado:
- TX1: 0xAAA → 0xBBB (100 tokens) ✅ Confirmada
- TX2: 0xCCC → 0xDDD (50 tokens) ✅ Confirmada
- Recompensa: Sistema → 0xTuDireccion (100 tokens) ✅

Balances Actualizados:
- 0xAAA: 900 tokens (1000 - 100) ✅
- 0xBBB: 600 tokens (500 + 100) ✅
- 0xTuDireccion: 100 tokens (recompensa) ✅
```

## Configuración Actual

Puedes cambiar estos valores en tu archivo `.env`:

```env
# Dificultad del minado (más = más difícil = más seguro = más lento)
BLOCKCHAIN_DIFFICULTY=4

# Recompensa por minar un bloque
BLOCKCHAIN_MINING_REWARD=100
```

### Valores Recomendados:

- **Difficulty 2-3**: Para desarrollo/testing (rápido, ~1-5 segundos)
- **Difficulty 4**: Para producción pequeña (moderado, ~5-30 segundos)
- **Difficulty 5-6**: Para producción grande (lento, ~30 segundos - varios minutos)

## Preguntas Frecuentes

### ¿Cuánto Tarda en Minar?

Depende de la dificultad:
- Difficulty 2: ~1-2 segundos
- Difficulty 4: ~5-30 segundos
- Difficulty 6: ~30 segundos - varios minutos

### ¿Puedo Minar Sin Transacciones Pendientes?

No, el sistema requiere al menos 1 transacción pendiente para minar. Si no hay transacciones, recibirás un mensaje de error.

### ¿Qué Pasa si Hay Muchas Transacciones Pendientes?

Todas se incluyen en el mismo bloque. El tiempo de minado es el mismo independientemente de cuántas transacciones haya.

### ¿Puedo Minar Varios Bloques Seguidos?

Sí, pero cada bloque debe tener transacciones pendientes. Si minas un bloque y no hay más transacciones pendientes, no podrás minar otro hasta que haya nuevas transacciones.

### ¿La Recompensa es Siempre la Misma?

Sí, por defecto es 100 tokens por bloque. Puedes cambiarlo en `.env` con `BLOCKCHAIN_MINING_REWARD`.

## Resumen Rápido

1. **Las transacciones quedan pendientes** hasta que se minan
2. **Minar = crear un bloque** con todas las transacciones pendientes
3. **El proceso busca un hash** que empiece con ceros (según la dificultad)
4. **Al encontrar el hash**, el bloque se guarda y las transacciones se confirman
5. **Recibes una recompensa** por minar el bloque
6. **Los balances se actualizan** automáticamente

¡Es así de simple! 🎉

