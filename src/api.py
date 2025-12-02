from fastapi import FastAPI, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
from src.blockchain_service import get_blockchain_service
from src.models import Transaction, Block
from src.wallet import wallet_manager
from src.utils import parse_amount, format_amount
from src.auth import create_access_token, verify_token, verify_signature, create_auth_message
from src.celery_app import celery_app
from src.tasks import (
    mine_block_task,
    process_transaction_task,
    validate_chain_task,
    update_cache_task,
    batch_process_transactions_task
)
import uvicorn
from src.config import settings
import os
import asyncio
import threading

from src.websocket_manager import ws_manager
from src.rabbitmq_client import RabbitMQClient

security = HTTPBearer()

# Función helper para obtener el servicio
def blockchain_service():
    return get_blockchain_service()

app = FastAPI(title="Blockchain Centralizada API", version="1.0.0")

# Montar archivos estáticos para el explorador legacy
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Montar archivos estáticos del frontend Next.js
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "out")
if os.path.exists(frontend_dir):
    # Servir archivos estáticos de Next.js (_next contiene JS, CSS, etc.)
    next_static_dir = os.path.join(frontend_dir, "_next")
    if os.path.exists(next_static_dir):
        app.mount("/_next", StaticFiles(directory=next_static_dir), name="nextjs_static")


@app.on_event("startup")
async def startup_event():
    """
    Arranca un consumidor de RabbitMQ en un hilo separado para enviar
    actualizaciones en tiempo real a través de WebSocket.
    """
    loop = asyncio.get_event_loop()

    def consume_blocks():
        client = RabbitMQClient()
        try:
            client.initialize()
        except Exception as e:
            print(f"Error inicializando RabbitMQ para WebSockets: {e}")
            return

        def handle_block(block_data: dict):
            # Para cada bloque minado, notificamos a las direcciones afectadas
            try:
                from src.utils import format_amount
                affected_addresses = set()
                transactions = block_data.get("transactions", [])
                for tx in transactions:
                    sender = (tx.get("sender") or "").lower()
                    recipient = (tx.get("recipient") or "").lower()
                    if sender and sender != "sistema":
                        affected_addresses.add(sender)
                    if recipient:
                        affected_addresses.add(recipient)

                if not affected_addresses:
                    return

                blockchain = get_blockchain_service()

                for address in affected_addresses:
                    try:
                        balance_wei = blockchain.get_balance(address)
                        balance_formatted = format_amount(balance_wei)
                    except Exception as e:
                        print(f"Error obteniendo balance para {address}: {e}")
                        continue

                    message = {
                        "type": "balance_update",
                        "address": address,
                        "balance": balance_wei,
                        "balance_formatted": balance_formatted,
                        "source": "block_mined",
                        "block_index": block_data.get("index"),
                        "block_hash": block_data.get("hash"),
                    }
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.send_personal_message(address, message),
                        loop,
                    )
            except Exception as e:
                print(f"Error manejando bloque para WebSockets: {e}")

        client.consume_blocks(handle_block)

    thread = threading.Thread(target=consume_blocks, daemon=True)
    thread.start()


# Dependencia para obtener el usuario autenticado
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Obtiene la dirección de la wallet del token JWT"""
    token = credentials.credentials
    address = verify_token(token)
    if address is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return address


class MiningRequest(BaseModel):
    mining_reward_address: str


class WalletGenerateRequest(BaseModel):
    account_index: int = 0


class WalletImportRequest(BaseModel):
    mnemonic: str
    account_index: int = 0


class AddressTransactionsRequest(BaseModel):
    address: str


class AuthRequest(BaseModel):
    address: str
    signature: str
    message: str


class AuthenticatedTransactionRequest(BaseModel):
    recipient: str
    amount: float


class AuthRequest(BaseModel):
    address: str
    signature: str
    message: str


class TransactionRequest(BaseModel):
    sender: str
    recipient: str
    amount: float


class AuthenticatedTransactionRequest(BaseModel):
    recipient: str
    amount: float


# Root endpoint movido más abajo para servir el frontend


@app.get("/chain")
async def get_chain():
    try:
        chain = blockchain_service().get_chain()
        return {
            "chain": [
                {
                    "index": block.index,
                    "timestamp": block.timestamp.isoformat(),
                    "transactions": [tx.to_dict() for tx in block.transactions],
                    "previous_hash": block.previous_hash,
                    "hash": block.hash,
                    "nonce": block.nonce
                }
                for block in chain
            ],
            "length": len(chain)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/wallet/{address}")
async def wallet_websocket(websocket: WebSocket, address: str):
    """
    WebSocket para actualizaciones de balance de una dirección específica.
    El servidor enviará mensajes con:
    {
      "type": "balance_update",
      "address": "...",
      "balance": <int>,              # en wei
      "balance_formatted": "<str>",  # formateado
      "source": "block_mined",
      "block_index": <int | null>,
      "block_hash": "<str | null>"
    }
    """
    await ws_manager.connect(address, websocket)
    try:
        while True:
            # Por ahora ignoramos mensajes del cliente; se podría usar para pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(address, websocket)
    except Exception:
        await ws_manager.disconnect(address, websocket)


@app.get("/chain/info")
async def get_chain_info():
    try:
        return blockchain_service().get_chain_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chain/validate")
async def validate_chain():
    try:
        is_valid = blockchain_service().is_chain_valid()
        return {"is_valid": is_valid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions/new")
async def create_transaction(transaction: TransactionRequest, async_mode: bool = False):
    """
    Crea una nueva transacción
    - async_mode=False: Procesa de forma síncrona (default)
    - async_mode=True: Procesa de forma asíncrona con Celery
    """
    """
    Crea una nueva transacción
    async_mode: Si es True, procesa la transacción de forma asíncrona con Celery
    """
    try:
        # Validar y convertir el monto a wei (entero)
        amount_wei = parse_amount(transaction.amount)
        
        if amount_wei <= 0:
            raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0")
        
        if async_mode:
            # Procesar de forma asíncrona con Celery
            task = process_transaction_task.delay(
                transaction.sender,
                transaction.recipient,
                float(transaction.amount)
            )
            return {
                "message": "Transacción en proceso (modo asíncrono)",
                "task_id": task.id,
                "status": "PENDING",
                "transaction": {
                    "sender": transaction.sender,
                    "recipient": transaction.recipient,
                    "amount": transaction.amount
                }
            }
        else:
            # Procesar de forma síncrona (comportamiento original)
            success = blockchain_service().add_transaction(
                transaction.sender,
                transaction.recipient,
                float(transaction.amount)
            )
            
            if success:
                return {
                    "message": "Transacción agregada exitosamente",
                    "transaction": {
                        "sender": transaction.sender,
                        "recipient": transaction.recipient,
                        "amount": transaction.amount
                    }
                }
            else:
                raise HTTPException(status_code=500, detail="Error al agregar transacción")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transactions/pending")
async def get_pending_transactions():
    try:
        pending = blockchain_service().get_pending_transactions()
        return {
            "pending_transactions": [tx.to_dict() for tx in pending],
            "count": len(pending)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mine")
async def mine_block(mining_request: MiningRequest, async_mode: bool = True):
    """
    Mina un bloque con las transacciones pendientes
    - async_mode=True: Mina de forma asíncrona con Celery (default, recomendado)
    - async_mode=False: Mina de forma síncrona (puede tardar mucho tiempo)
    """
    try:
        if async_mode:
            # Minar de forma asíncrona con Celery
            task = mine_block_task.delay(mining_request.mining_reward_address)
            return {
                "message": "Minería iniciada (modo asíncrono)",
                "task_id": task.id,
                "status": "PENDING",
                "mining_reward_address": mining_request.mining_reward_address
            }
        else:
            # Minar de forma síncrona (comportamiento original)
            block = blockchain_service().mine_pending_transactions(
                mining_reward_address=mining_request.mining_reward_address,
                include_reward=True
            )
            
            if block:
                return {
                    "message": "Bloque minado exitosamente",
                    "block": {
                        "index": block.index,
                        "timestamp": block.timestamp.isoformat(),
                        "transactions": [tx.to_dict() for tx in block.transactions],
                        "previous_hash": block.previous_hash,
                        "hash": block.hash,
                        "nonce": block.nonce
                    }
                }
            else:
                raise HTTPException(status_code=500, detail="Error al minar bloque")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/balance/{address}")
async def get_balance(address: str):
    try:
        balance_wei = blockchain_service().get_balance(address)  # Balance en wei (entero)
        return {
            "address": address,
            "balance": balance_wei,  # Balance en wei (entero)
            "balance_formatted": format_amount(balance_wei)  # Formato legible con decimales
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/block/{hash}")
async def get_block_by_hash(hash: str):
    try:
        block = blockchain_service().get_block_by_hash(hash)
        if block:
            return {
                "index": block.index,
                "timestamp": block.timestamp.isoformat(),
                "transactions": [tx.to_dict() for tx in block.transactions],
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "nonce": block.nonce
            }
        else:
            raise HTTPException(status_code=404, detail="Bloque no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transaction/{tx_hash}")
async def get_transaction_by_hash(tx_hash: str):
    """Busca una transacción por su hash"""
    try:
        result = blockchain_service().get_transaction_by_hash(tx_hash)
        if result:
            return result
        else:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/explorer")
async def explorer():
    """Sirve el explorador web (legacy HTML)"""
    explorer_path = os.path.join(os.path.dirname(__file__), "..", "static", "explorer.html")
    if os.path.exists(explorer_path):
        return FileResponse(explorer_path)
    raise HTTPException(status_code=404, detail="Explorador no encontrado")


@app.get("/")
async def root():
    """Sirve el frontend de Next.js"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "out", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    # Fallback al explorador HTML si Next.js no está construido
    explorer_path = os.path.join(os.path.dirname(__file__), "..", "static", "explorer.html")
    if os.path.exists(explorer_path):
        return FileResponse(explorer_path)
    return {"message": "Blockchain Centralizada API", "version": "1.0.0", "frontend": "Next.js no construido aún. Ejecuta: cd frontend && npm install && npm run build"}


@app.post("/auth/login")
async def login(auth_request: AuthRequest):
    """Autentica una wallet usando MetaMask"""
    try:
        if not wallet_manager.verify_address(auth_request.address):
            raise HTTPException(status_code=400, detail="Dirección inválida")
        
        # Verificar la firma del mensaje
        if not verify_signature(auth_request.message, auth_request.signature, auth_request.address):
            raise HTTPException(status_code=401, detail="Firma inválida")
        
        # Crear token de acceso
        token = create_access_token(auth_request.address)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "address": auth_request.address,
            "expires_in_hours": 24
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/message/{address}")
async def get_auth_message(address: str):
    """Obtiene el mensaje que debe firmarse para autenticación"""
    try:
        if not wallet_manager.verify_address(address):
            raise HTTPException(status_code=400, detail="Dirección inválida")
        
        message = create_auth_message(address)
        return {
            "message": message,
            "address": address
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions/transfer")
async def transfer_funds(
    transaction: AuthenticatedTransactionRequest,
    current_user: str = Depends(get_current_user)
):
    """Crea una transacción usando la wallet autenticada"""
    try:
        if not wallet_manager.verify_address(transaction.recipient):
            raise HTTPException(status_code=400, detail="Dirección del destinatario inválida")
        
        # Usar la dirección autenticada como remitente
        success = blockchain_service().add_transaction(
            current_user,
            transaction.recipient,
            transaction.amount
        )
        
        if success:
            return {
                "message": "Transacción creada exitosamente",
                "transaction": {
                    "sender": current_user,
                    "recipient": transaction.recipient,
                    "amount": transaction.amount
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Error al crear transacción")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/balance")
async def get_my_balance(current_user: str = Depends(get_current_user)):
    """Obtiene el balance de la wallet autenticada"""
    try:
        balance_wei = blockchain_service().get_balance(current_user)
        return {
            "address": current_user,
            "balance": balance_wei,
            "balance_formatted": format_amount(balance_wei)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/transactions")
async def get_my_transactions(current_user: str = Depends(get_current_user)):
    """Obtiene las transacciones de la wallet autenticada"""
    try:
        transactions = []
        chain = blockchain_service().get_chain()
        
        current_user_lower = current_user.lower()
        for block in chain:
            for tx in block.transactions:
                sender_lower = tx.sender.lower() if tx.sender else ""
                recipient_lower = tx.recipient.lower() if tx.recipient else ""
                
                if sender_lower == current_user_lower or recipient_lower == current_user_lower:
                    transactions.append({
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                        "sender": tx.sender,
                        "recipient": tx.recipient,
                        "amount": tx.amount,
                        "amount_formatted": format_amount(tx.amount),
                        "type": "sent" if sender_lower == current_user_lower else "received",
                        "hash": tx.calculate_hash()
                    })
        
        return {
            "address": current_user,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wallet/generate")
async def generate_wallet(request: WalletGenerateRequest):
    """Genera una nueva wallet con mnemonic de 12 palabras"""
    try:
        wallet = wallet_manager.generate_new_wallet(account_index=request.account_index)
        return {
            "success": True,
            "wallet": {
                "address": wallet["address"],
                "mnemonic": wallet["mnemonic"],
                "account_index": wallet["account_index"],
                "derivation_path": wallet["derivation_path"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wallet/import")
async def import_wallet(request: WalletImportRequest):
    """Importa una wallet desde un mnemonic"""
    try:
        wallet = wallet_manager.import_wallet_from_mnemonic(
            request.mnemonic,
            account_index=request.account_index
        )
        balance = blockchain_service().get_balance(wallet["address"])
        return {
            "success": True,
            "wallet": {
                "address": wallet["address"],
                "account_index": wallet["account_index"],
                "derivation_path": wallet["derivation_path"],
                "balance": balance
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/{address}/balance")
async def get_wallet_balance(address: str):
    """Obtiene el balance de una dirección"""
    try:
        if not wallet_manager.verify_address(address):
            raise HTTPException(status_code=400, detail="Dirección inválida")
        balance_wei = blockchain_service().get_balance(address)  # Balance en wei (entero)
        return {
            "address": address,
            "balance": balance_wei,  # Balance en wei (entero)
            "balance_formatted": format_amount(balance_wei)  # Formato legible con decimales
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/{address}/transactions")
async def get_address_transactions(address: str):
    """Obtiene todas las transacciones de una dirección"""
    try:
        if not wallet_manager.verify_address(address):
            raise HTTPException(status_code=400, detail="Dirección inválida")
        
        transactions = []
        chain = blockchain_service().get_chain()
        
        for block in chain:
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    transactions.append({
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                        "sender": tx.sender,
                        "recipient": tx.recipient,
                        "amount": tx.amount,
                        "amount_formatted": format_amount(tx.amount),
                        "type": "sent" if tx.sender == address else "received"
                    })
        
        return {
            "address": address,
            "transactions": transactions,
            "count": len(transactions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Endpoints de Celery ====================

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Obtiene el estado de una tarea Celery"""
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'La tarea está esperando ser procesada'
            }
        elif task.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'La tarea está en progreso',
                'info': task.info
            }
        elif task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Tarea completada exitosamente',
                'result': task.result
            }
        else:
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': f'Estado: {task.state}',
                'error': str(task.info) if task.info else None
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/validate-chain")
async def validate_chain_async():
    """Valida la cadena de forma asíncrona"""
    try:
        task = validate_chain_task.delay()
        return {
            "message": "Validación iniciada (modo asíncrono)",
            "task_id": task.id,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/update-cache")
async def update_cache_async():
    """Actualiza la caché de forma asíncrona"""
    try:
        task = update_cache_task.delay()
        return {
            "message": "Actualización de caché iniciada",
            "task_id": task.id,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BatchTransactionRequest(BaseModel):
    transactions: List[Dict[str, str]]


@app.post("/transactions/batch")
async def batch_create_transactions(batch_request: BatchTransactionRequest, async_mode: bool = True):
    """Crea múltiples transacciones en lote"""
    try:
        if async_mode:
            task = batch_process_transactions_task.delay(batch_request.transactions)
            return {
                "message": "Procesamiento en lote iniciado (modo asíncrono)",
                "task_id": task.id,
                "status": "PENDING",
                "total_transactions": len(batch_request.transactions)
            }
        else:
            results = []
            for tx in batch_request.transactions:
                try:
                    success = blockchain_service().add_transaction(
                        tx['sender'],
                        tx['recipient'],
                        float(tx['amount'])
                    )
                    results.append({
                        "success": success,
                        "transaction": tx
                    })
                except Exception as e:
                    results.append({
                        "success": False,
                        "transaction": tx,
                        "error": str(e)
                    })
            
            return {
                "message": "Lote procesado",
                "results": results,
                "total": len(results),
                "success_count": sum(1 for r in results if r['success'])
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/financial/report")
async def get_financial_report():
    """Genera un reporte financiero completo de la blockchain"""
    try:
        report = blockchain_service().get_financial_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Sirve archivos estáticos del frontend Next.js para rutas no-API"""
    # Esta ruta catch-all debe estar al final, después de todas las rutas de API
    # Si llegamos aquí, significa que ninguna ruta de API coincidió
    
    # Intentar servir desde el frontend construido
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "out")
    file_path = os.path.join(frontend_dir, path)
    
    # Si es un directorio o no existe, servir index.html (SPA routing)
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    
    # Si existe el archivo, servirlo
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="Not found")


def run_api():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.BLOCKCHAIN_API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )

