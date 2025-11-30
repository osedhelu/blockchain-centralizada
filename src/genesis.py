import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from src.models import Transaction
from src.utils import parse_amount, format_amount


class GenesisLoader:
    def __init__(self, genesis_file: str = "genesis.json"):
        self.genesis_file = genesis_file
        self.genesis_data = None
    
    def load_genesis(self) -> Optional[Dict]:
        """Carga el archivo genesis.json"""
        try:
            # Buscar el archivo en el directorio raíz del proyecto
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            genesis_path = os.path.join(project_root, self.genesis_file)
            
            if not os.path.exists(genesis_path):
                print(f"Archivo genesis.json no encontrado en {genesis_path}. Usando bloque génesis vacío.")
                return None
            
            with open(genesis_path, 'r', encoding='utf-8') as f:
                self.genesis_data = json.load(f)
            
            print(f"✓ Genesis cargado desde {genesis_path}")
            return self.genesis_data
        except json.JSONDecodeError as e:
            print(f"Error parseando genesis.json: {e}")
            return None
        except Exception as e:
            print(f"Error cargando genesis.json: {e}")
            return None
    
    def get_genesis_transactions(self) -> List[Transaction]:
        """Obtiene las transacciones del bloque génesis"""
        transactions = []
        
        if not self.genesis_data:
            return transactions
        
        allocations = self.genesis_data.get('genesis_allocations', [])
        
        for allocation in allocations:
            address = allocation.get('address', '').strip()
            amount_raw = allocation.get('amount', 0)
            description = allocation.get('description', '')
            
            if not address:
                print(f"⚠️  Advertencia: Dirección vacía en allocation, saltando...")
                continue
            
            # Parsear y convertir el monto a wei (entero)
            try:
                amount_wei = parse_amount(amount_raw)  # Convierte a wei (entero)
            except Exception as e:
                print(f"⚠️  Advertencia: Error parseando monto ({amount_raw}) para dirección {address}: {e}")
                continue
            
            if amount_wei <= 0:
                print(f"⚠️  Advertencia: Monto inválido ({amount_wei}) para dirección {address}, saltando...")
                continue
            
            # Crear transacción desde "Sistema" (dirección especial del génesis)
            transaction = Transaction(
                sender="Sistema",
                recipient=address,
                amount=amount_wei,  # Monto en wei (entero)
                timestamp=datetime.now()
            )
            transactions.append(transaction)
            print(f"  ✓ Asignación génesis: {format_amount(amount_wei)} → {address} ({description})")
        
        total_allocated_wei = sum(tx.amount for tx in transactions)  # Suma de wei (enteros)
        if transactions:
            print(f"✓ Total asignado en génesis: {format_amount(total_allocated_wei)}")
        
        return transactions
    
    def get_genesis_timestamp(self) -> Optional[datetime]:
        """Obtiene el timestamp del génesis si está especificado"""
        if not self.genesis_data:
            return None
        
        timestamp_str = self.genesis_data.get('genesis_timestamp')
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except:
                return None
        
        return None


genesis_loader = GenesisLoader()

