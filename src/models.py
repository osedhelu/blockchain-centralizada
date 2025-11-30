from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
import hashlib
import json
from src.utils import parse_amount, format_amount


class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: int  # Monto en wei (entero sin decimales)
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        # Convertir el monto a wei (entero)
        if 'amount' in data:
            data['amount'] = parse_amount(data['amount'])
        super().__init__(**data)
    
    def calculate_hash(self) -> str:
        """Calcula el hash único de la transacción"""
        import hashlib
        tx_string = json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': str(self.amount),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return {
            'hash': self.calculate_hash(),
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,  # Monto en wei (entero)
            'amount_formatted': format_amount(self.amount),  # Formato legible
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Block(BaseModel):
    index: int
    timestamp: datetime
    transactions: List[Transaction]
    previous_hash: str
    hash: str
    nonce: int
    
    def calculate_hash(self) -> str:
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp.isoformat(),
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()


class Blockchain(BaseModel):
    chain: List[Block]
    pending_transactions: List[Transaction]
    difficulty: int
    mining_reward: float
    
    def __init__(self, difficulty: int = 4, mining_reward: float = 100.0, genesis_transactions: List[Transaction] = None):
        super().__init__(
            chain=[],
            pending_transactions=[],
            difficulty=difficulty,
            mining_reward=mining_reward
        )
        self.create_genesis_block(genesis_transactions)
    
    def create_genesis_block(self, genesis_transactions: List[Transaction] = None) -> None:
        """Crea el bloque génesis con transacciones opcionales"""
        if genesis_transactions is None:
            genesis_transactions = []
        
        genesis_block = Block(
            index=0,
            timestamp=datetime.now(),
            transactions=genesis_transactions,
            previous_hash="0",
            hash="",
            nonce=0
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> None:
        self.pending_transactions.append(transaction)
    
    def mine_pending_transactions(self, mining_reward_address: str) -> None:
        # Convertir mining_reward a wei
        from src.utils import to_wei
        reward_wei = to_wei(self.mining_reward)
        reward_tx = Transaction(
            sender="Sistema",
            recipient=mining_reward_address,
            amount=reward_wei
        )
        self.pending_transactions.append(reward_tx)
        
        block = Block(
            index=len(self.chain),
            timestamp=datetime.now(),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash,
            hash="",
            nonce=0
        )
        
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
    
    def get_balance(self, address: str) -> int:
        """
        Retorna el balance en wei (entero sin decimales)
        Comparación case-insensitive de direcciones
        """
        balance = 0
        # Normalizar la dirección a minúsculas para comparación
        address_lower = address.lower() if address else ""
        
        for block in self.chain:
            for transaction in block.transactions:
                # Comparar en minúsculas para evitar problemas de case sensitivity
                sender_lower = transaction.sender.lower() if transaction.sender else ""
                recipient_lower = transaction.recipient.lower() if transaction.recipient else ""
                
                if sender_lower == address_lower:
                    balance -= transaction.amount
                if recipient_lower == address_lower:
                    balance += transaction.amount
        return balance
    
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True

