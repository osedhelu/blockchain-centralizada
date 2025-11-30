from src.models import Blockchain, Transaction, Block
from src.database import db
from src.redis_client import redis_client
from src.rabbitmq_client import rabbitmq_client
from src.config import settings
from typing import List, Optional


class BlockchainService:
    def __init__(self):
        self.blockchain = None
        self._initialize_blockchain()
    
    def _initialize_blockchain(self):
        try:
            blocks = db.get_all_blocks()
            if blocks:
                self.blockchain = Blockchain(
                    difficulty=settings.BLOCKCHAIN_DIFFICULTY,
                    mining_reward=settings.BLOCKCHAIN_MINING_REWARD
                )
                self.blockchain.chain = blocks
                print(f"Blockchain cargada desde BD: {len(blocks)} bloques")
            else:
                self.blockchain = Blockchain(
                    difficulty=settings.BLOCKCHAIN_DIFFICULTY,
                    mining_reward=settings.BLOCKCHAIN_MINING_REWARD
                )
                genesis_block = self.blockchain.chain[0]
                db.save_block(genesis_block)
                print("Blockchain nueva creada")
        except Exception as e:
            print(f"Error inicializando blockchain: {e}")
            self.blockchain = Blockchain(
                difficulty=settings.BLOCKCHAIN_DIFFICULTY,
                mining_reward=settings.BLOCKCHAIN_MINING_REWARD
            )
    
    def add_transaction(self, sender: str, recipient: str, amount: float) -> bool:
        try:
            transaction = Transaction(
                sender=sender,
                recipient=recipient,
                amount=amount
            )
            self.blockchain.add_transaction(transaction)
            redis_client.cache_pending_transactions(self.blockchain.pending_transactions)
            rabbitmq_client.publish_transaction(transaction)
            return True
        except Exception as e:
            print(f"Error agregando transacción: {e}")
            return False
    
    def mine_pending_transactions(self, mining_reward_address: str) -> Optional[Block]:
        try:
            self.blockchain.mine_pending_transactions(mining_reward_address)
            latest_block = self.blockchain.get_latest_block()
            
            if db.save_block(latest_block):
                redis_client.cache_blockchain_state(
                    len(self.blockchain.chain),
                    latest_block.hash
                )
                rabbitmq_client.publish_block(latest_block)
                return latest_block
            return None
        except Exception as e:
            print(f"Error minando transacciones: {e}")
            return None
    
    def get_balance(self, address: str) -> float:
        return self.blockchain.get_balance(address)
    
    def get_chain(self) -> List[Block]:
        return self.blockchain.chain
    
    def get_pending_transactions(self) -> List[Transaction]:
        return self.blockchain.pending_transactions
    
    def get_block_by_hash(self, hash: str) -> Optional[Block]:
        return db.get_block_by_hash(hash)
    
    def is_chain_valid(self) -> bool:
        return self.blockchain.is_chain_valid()
    
    def get_chain_info(self) -> dict:
        return {
            'length': len(self.blockchain.chain),
            'difficulty': self.blockchain.difficulty,
            'mining_reward': self.blockchain.mining_reward,
            'pending_transactions': len(self.blockchain.pending_transactions),
            'is_valid': self.is_chain_valid()
        }


blockchain_service = BlockchainService()

