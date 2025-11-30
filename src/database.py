import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager
from src.config import settings
from src.utils import parse_amount
import json
from datetime import datetime
from typing import List, Optional
from src.models import Block, Transaction


class Database:
    def __init__(self):
        self.connection_pool = None
    
    def initialize(self):
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD
            )
            self.create_tables()
        except Exception as e:
            print(f"Error inicializando base de datos: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)
    
    def create_tables(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS blocks (
                        id SERIAL PRIMARY KEY,
                        index INTEGER NOT NULL UNIQUE,
                        timestamp TIMESTAMP NOT NULL,
                        previous_hash VARCHAR(255) NOT NULL,
                        hash VARCHAR(255) NOT NULL UNIQUE,
                        nonce INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        block_index INTEGER,
                        sender VARCHAR(255) NOT NULL,
                        recipient VARCHAR(255) NOT NULL,
                        amount NUMERIC(78, 0) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        FOREIGN KEY (block_index) REFERENCES blocks(index) ON DELETE CASCADE
                    );
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks(hash);
                    CREATE INDEX IF NOT EXISTS idx_blocks_index ON blocks(index);
                    CREATE INDEX IF NOT EXISTS idx_transactions_block_index ON transactions(block_index);
                """)
    
    def save_block(self, block: Block) -> bool:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO blocks (index, timestamp, previous_hash, hash, nonce)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (hash) DO NOTHING
                        RETURNING id;
                    """, (
                        block.index,
                        block.timestamp,
                        block.previous_hash,
                        block.hash,
                        block.nonce
                    ))
                    
                    result = cur.fetchone()
                    if result:
                        block_id = result[0]
                        for tx in block.transactions:
                            cur.execute("""
                                INSERT INTO transactions (block_index, sender, recipient, amount, timestamp)
                                VALUES (%s, %s, %s, %s, %s);
                            """, (
                                block.index,
                                tx.sender,
                                tx.recipient,
                                int(tx.amount),  # Asegurar que es entero
                                tx.timestamp
                            ))
                        return True
                    return False
        except Exception as e:
            print(f"Error guardando bloque: {e}")
            return False
    
    def get_all_blocks(self) -> List[Block]:
        blocks = []
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM blocks ORDER BY index ASC;
                    """)
                    block_rows = cur.fetchall()
                    
                    for block_row in block_rows:
                        cur.execute("""
                            SELECT sender, recipient, amount, timestamp
                            FROM transactions
                            WHERE block_index = %s
                            ORDER BY id ASC;
                        """, (block_row['index'],))
                        
                        tx_rows = cur.fetchall()
                        transactions = [
                            Transaction(
                                sender=tx['sender'],
                                recipient=tx['recipient'],
                                amount=int(tx['amount']),  # Ya está en wei (entero)
                                timestamp=tx['timestamp']
                            )
                            for tx in tx_rows
                        ]
                        
                        block = Block(
                            index=block_row['index'],
                            timestamp=block_row['timestamp'],
                            transactions=transactions,
                            previous_hash=block_row['previous_hash'],
                            hash=block_row['hash'],
                            nonce=block_row['nonce']
                        )
                        blocks.append(block)
        except Exception as e:
            print(f"Error obteniendo bloques: {e}")
        
        return blocks
    
    def get_block_by_hash(self, hash: str) -> Optional[Block]:
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM blocks WHERE hash = %s;
                    """, (hash,))
                    block_row = cur.fetchone()
                    
                    if not block_row:
                        return None
                    
                    cur.execute("""
                        SELECT sender, recipient, amount, timestamp
                        FROM transactions
                        WHERE block_index = %s
                        ORDER BY id ASC;
                    """, (block_row['index'],))
                    
                    tx_rows = cur.fetchall()
                    transactions = [
                        Transaction(
                            sender=tx['sender'],
                            recipient=tx['recipient'],
                            amount=float(parse_amount(str(tx['amount']))),
                            timestamp=tx['timestamp']
                        )
                        for tx in tx_rows
                    ]
                    
                    return Block(
                        index=block_row['index'],
                        timestamp=block_row['timestamp'],
                        transactions=transactions,
                        previous_hash=block_row['previous_hash'],
                        hash=block_row['hash'],
                        nonce=block_row['nonce']
                    )
        except Exception as e:
            print(f"Error obteniendo bloque por hash: {e}")
            return None
    
    def get_latest_block(self) -> Optional[Block]:
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM blocks ORDER BY index DESC LIMIT 1;
                    """)
                    block_row = cur.fetchone()
                    
                    if not block_row:
                        return None
                    
                    cur.execute("""
                        SELECT sender, recipient, amount, timestamp
                        FROM transactions
                        WHERE block_index = %s
                        ORDER BY id ASC;
                    """, (block_row['index'],))
                    
                    tx_rows = cur.fetchall()
                    transactions = [
                        Transaction(
                            sender=tx['sender'],
                            recipient=tx['recipient'],
                            amount=float(parse_amount(str(tx['amount']))),
                            timestamp=tx['timestamp']
                        )
                        for tx in tx_rows
                    ]
                    
                    return Block(
                        index=block_row['index'],
                        timestamp=block_row['timestamp'],
                        transactions=transactions,
                        previous_hash=block_row['previous_hash'],
                        hash=block_row['hash'],
                        nonce=block_row['nonce']
                    )
        except Exception as e:
            print(f"Error obteniendo último bloque: {e}")
            return None


db = Database()

