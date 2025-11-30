from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import hashlib
import json


class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: float
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)
    
    def to_dict(self) -> dict:
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
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
    
    def __init__(self, difficulty: int = 4, mining_reward: float = 100.0):
        super().__init__(
            chain=[],
            pending_transactions=[],
            difficulty=difficulty,
            mining_reward=mining_reward
        )
        self.create_genesis_block()
    
    def create_genesis_block(self) -> None:
        genesis_block = Block(
            index=0,
            timestamp=datetime.now(),
            transactions=[],
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
        reward_tx = Transaction(
            sender="Sistema",
            recipient=mining_reward_address,
            amount=self.mining_reward
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
    
    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == address:
                    balance -= transaction.amount
                if transaction.recipient == address:
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

