import jwt
import time
from datetime import datetime, timedelta
from typing import Optional
from src.config import settings
from src.wallet import wallet_manager
from eth_account.messages import encode_defunct
from eth_account import Account


# Clave secreta para firmar tokens (en producción usar variable de entorno)
SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 24


def create_access_token(address: str) -> str:
    """Crea un token JWT para una dirección de wallet"""
    expiration = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
    payload = {
        "address": address.lower(),
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> Optional[str]:
    """Verifica un token JWT y retorna la dirección si es válido"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        address = payload.get("address")
        return address.lower() if address else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_signature(message: str, signature: str, address: str) -> bool:
    """Verifica que la firma del mensaje corresponde a la dirección"""
    try:
        # Crear mensaje firmable
        message_hash = encode_defunct(text=message)
        
        # Recuperar la dirección del firmante
        recovered_address = Account.recover_message(message_hash, signature=signature)
        
        # Comparar direcciones (case-insensitive)
        return recovered_address.lower() == address.lower()
    except Exception as e:
        print(f"Error verificando firma: {e}")
        return False


def create_auth_message(address: str) -> str:
    """Crea un mensaje único para autenticación"""
    timestamp = int(time.time())
    return f"Autenticación Blockchain Centralizada\n\nDirección: {address}\nTimestamp: {timestamp}\n\nFirma este mensaje para autenticarte."

