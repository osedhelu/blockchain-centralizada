from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from src.blockchain_service import blockchain_service
from src.models import Transaction, Block
from src.wallet import wallet_manager
import uvicorn
from src.config import settings
import os

app = FastAPI(title="Blockchain Centralizada API", version="1.0.0")

# Montar archivos estáticos para el explorador
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class TransactionRequest(BaseModel):
    sender: str
    recipient: str
    amount: float


class MiningRequest(BaseModel):
    mining_reward_address: str


class WalletGenerateRequest(BaseModel):
    account_index: int = 0


class WalletImportRequest(BaseModel):
    mnemonic: str
    account_index: int = 0


class AddressTransactionsRequest(BaseModel):
    address: str


@app.get("/")
async def root():
    return {"message": "Blockchain Centralizada API", "version": "1.0.0"}


@app.get("/chain")
async def get_chain():
    try:
        chain = blockchain_service.get_chain()
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


@app.get("/chain/info")
async def get_chain_info():
    try:
        return blockchain_service.get_chain_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chain/validate")
async def validate_chain():
    try:
        is_valid = blockchain_service.is_chain_valid()
        return {"is_valid": is_valid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions/new")
async def create_transaction(transaction: TransactionRequest):
    try:
        if transaction.amount <= 0:
            raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0")
        
        success = blockchain_service.add_transaction(
            transaction.sender,
            transaction.recipient,
            transaction.amount
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
        pending = blockchain_service.get_pending_transactions()
        return {
            "pending_transactions": [tx.to_dict() for tx in pending],
            "count": len(pending)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mine")
async def mine_block(mining_request: MiningRequest):
    try:
        block = blockchain_service.mine_pending_transactions(
            mining_request.mining_reward_address
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
        balance = blockchain_service.get_balance(address)
        return {"address": address, "balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/block/{hash}")
async def get_block_by_hash(hash: str):
    try:
        block = blockchain_service.get_block_by_hash(hash)
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


@app.get("/explorer")
async def explorer():
    """Sirve el explorador web"""
    explorer_path = os.path.join(os.path.dirname(__file__), "..", "static", "explorer.html")
    if os.path.exists(explorer_path):
        return FileResponse(explorer_path)
    raise HTTPException(status_code=404, detail="Explorador no encontrado")


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
        balance = blockchain_service.get_balance(wallet["address"])
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
        balance = blockchain_service.get_balance(address)
        return {
            "address": address,
            "balance": balance
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
        chain = blockchain_service.get_chain()
        
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


def run_api():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.BLOCKCHAIN_API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )

