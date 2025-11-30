# Configuración del Bloque Génesis

El bloque génesis permite asignar montos iniciales a wallets específicas cuando se crea la blockchain por primera vez.

## Archivo genesis.json

Crea un archivo `genesis.json` en la raíz del proyecto basándote en `genesis.json.example`:

```bash
cp genesis.json.example genesis.json
```

## Estructura del archivo genesis.json

```json
{
  "genesis_allocations": [
    {
      "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "amount": "1000000000000000000000000",
      "description": "Wallet principal del sistema (1,000,000 tokens)"
    },
    {
      "address": "0x8ba1f109551bD432803012645Hac136c22C1779",
      "amount": "500000123456789012345678",
      "description": "Wallet de desarrollo (500,000.123456789012345678 tokens)"
    }
  ],
  "genesis_timestamp": null,
  "genesis_note": "Bloque génesis con asignaciones iniciales"
}
```

### Campos

- **genesis_allocations**: Array de objetos con las asignaciones iniciales
  - **address**: Dirección de la wallet (formato Ethereum 0x...)
  - **amount**: Monto inicial a asignar (entero en wei o decimal que se convierte automáticamente)
    - Ejemplo: "1000000000000000000000000" (1,000,000 tokens en wei)
    - Ejemplo: "1.5" (se convierte a 1500000000000000000 wei)
  - **description**: Descripción opcional de la wallet
  
- **genesis_timestamp**: Timestamp opcional para el bloque génesis (null = usar timestamp actual)
  - Formato: ISO 8601 (ej: "2024-01-01T00:00:00")

- **genesis_note**: Nota opcional sobre el génesis

## Ejemplo de uso

### 1. Generar wallets

Primero genera las wallets que quieres usar:

```bash
# Generar wallet 1
python generate_wallet.py --index 0

# Generar wallet 2
python generate_wallet.py --index 1

# Generar wallet 3
python generate_wallet.py --index 2
```

### 2. Crear genesis.json

Copia las direcciones generadas y crea tu `genesis.json`:

```json
{
  "genesis_allocations": [
    {
      "address": "0xTuDireccionWallet1",
      "amount": "1000000000000000000000000",
      "description": "Mi wallet principal (1,000,000 tokens)"
    },
    {
      "address": "0xTuDireccionWallet2",
      "amount": "500000000000000000000000",
      "description": "Wallet secundaria (500,000 tokens)"
    },
    {
      "address": "0xTuDireccionWallet3",
      "amount": "250000000000000000000000",
      "description": "Wallet de pruebas (250,000 tokens)"
    }
  ],
  "genesis_timestamp": null,
  "genesis_note": "Asignaciones iniciales para mi blockchain"
}
```

**Nota**: También puedes usar decimales y el sistema los convertirá automáticamente:
```json
{
  "address": "0xTuDireccionWallet1",
  "amount": "1.5",
  "description": "Se convierte a 1500000000000000000 wei"
}
```

### 3. Iniciar la blockchain

```bash
docker-compose down -v  # Elimina datos existentes
docker-compose up -d    # Inicia con el nuevo génesis
```

## Verificar asignaciones

Una vez iniciada la blockchain, puedes verificar los balances:

```bash
# Ver balance de una wallet
curl http://localhost:8000/wallet/0xTuDireccion/balance

# O usar el explorador web
# http://localhost:8000/explorer
```

## Notas importantes

1. **El archivo genesis.json solo se usa cuando se crea la blockchain por primera vez**
   - Si ya existe una blockchain, el génesis no se aplicará
   - Para aplicar un nuevo génesis, elimina los volúmenes: `docker-compose down -v`

2. **Las transacciones del génesis tienen como remitente "Sistema"**
   - Esto indica que son asignaciones iniciales, no transferencias entre wallets

3. **El archivo genesis.json no se versiona en git**
   - Está en `.gitignore` para mantener privadas tus asignaciones

4. **Puedes agregar tantas wallets como necesites**
   - No hay límite en el número de asignaciones

5. **Los montos se almacenan como enteros (wei) sin punto decimal**
   - Puedes usar enteros grandes directamente: "1000000000000000000000000" (1M tokens)
   - O usar decimales que se convierten automáticamente: "1.5" → 1500000000000000000 wei
   - Formato estándar ERC-20: 18 decimales implícitos, almacenados como enteros

## Ejemplo completo

```json
{
  "genesis_allocations": [
    {
      "address": "0x1111111111111111111111111111111111111111",
      "amount": "10000000000000000000000000",
      "description": "Fondo de reserva (10,000,000 tokens)"
    },
    {
      "address": "0x2222222222222222222222222222222222222222",
      "amount": "5000000000000000000000000",
      "description": "Fondo de desarrollo (5,000,000 tokens)"
    },
    {
      "address": "0x3333333333333333333333333333333333333333",
      "amount": "1000000123456789012345678",
      "description": "Fondo de marketing (1,000,000.123456789012345678 tokens)"
    },
    {
      "address": "0x4444444444444444444444444444444444444444",
      "amount": "500000000000000000000000",
      "description": "Fondo de pruebas (500,000 tokens)"
    }
  ],
  "genesis_timestamp": "2024-01-01T00:00:00",
  "genesis_note": "Distribución inicial de tokens"
}
```

