from mnemonic import Mnemonic
from eth_account import Account
from typing import Dict, Optional


class WalletManager:
    def __init__(self):
        Account.enable_unaudited_hdwallet_features()
    
    def generate_mnemonic(self, language: str = "english") -> str:
        """Genera un mnemonic de 12 palabras"""
        mnemo = Mnemonic(language)
        strength = 128
        mnemonic = mnemo.generate(strength=strength)
        return mnemonic
    
    def generate_wallet_from_mnemonic(self, mnemonic: str, account_index: int = 0) -> Dict[str, str]:
        """
        Genera una wallet desde un mnemonic usando derivación BIP44
        account_index: índice de la cuenta (0 para primera wallet, 1 para segunda, etc.)
        Ruta de derivación: m/44'/60'/{account_index}'/0/0
        """
        try:
            # Validar mnemonic
            mnemo = Mnemonic("english")
            if not mnemo.check(mnemonic):
                raise ValueError("Mnemonic inválido")
            
            # Usar hdwallet para derivación BIP44 correcta
            try:
                from hdwallet import HDWallet
                from hdwallet.symbols import ETH
                
                hdwallet = HDWallet(symbol=ETH)
                hdwallet.from_mnemonic(mnemonic=mnemonic)
                hdwallet.from_index(account_index)
                
                derivation_path = f"m/44'/60'/{account_index}'/0/0"
                
                return {
                    "mnemonic": mnemonic,
                    "private_key": hdwallet.private_key(),
                    "public_key": hdwallet.public_key(),
                    "address": hdwallet.address(),
                    "account_index": account_index,
                    "derivation_path": derivation_path
                }
            except ImportError:
                # Fallback: usar eth_account básico (solo funciona para account_index 0)
                if account_index != 0:
                    raise ValueError(
                        f"Para generar wallet en posición {account_index}, "
                        "necesitas instalar hdwallet: pip install hdwallet"
                    )
                
                account = Account.from_mnemonic(mnemonic)
                return {
                    "mnemonic": mnemonic,
                    "private_key": account.key.hex(),
                    "public_key": "",
                    "address": account.address,
                    "account_index": account_index,
                    "derivation_path": "m/44'/60'/0'/0/0"
                }
        except Exception as e:
            raise Exception(f"Error generando wallet: {e}")
    
    def generate_new_wallet(self, account_index: int = 0) -> Dict[str, str]:
        """Genera una nueva wallet con mnemonic de 12 palabras"""
        mnemonic = self.generate_mnemonic()
        return self.generate_wallet_from_mnemonic(mnemonic, account_index)
    
    def import_wallet_from_mnemonic(self, mnemonic: str, account_index: int = 0) -> Dict[str, str]:
        """Importa una wallet desde un mnemonic existente"""
        mnemo = Mnemonic("english")
        if not mnemo.check(mnemonic):
            raise ValueError("Mnemonic inválido")
        
        return self.generate_wallet_from_mnemonic(mnemonic, account_index)
    
    def import_wallet_from_private_key(self, private_key: str) -> Dict[str, str]:
        """Importa una wallet desde una clave privada"""
        try:
            account = Account.from_key(private_key)
            return {
                "address": account.address,
                "private_key": private_key,
                "public_key": account.key.hex()
            }
        except Exception as e:
            raise Exception(f"Error importando wallet desde clave privada: {e}")
    
    def sign_transaction(self, private_key: str, transaction_data: dict) -> str:
        """Firma una transacción con la clave privada"""
        try:
            account = Account.from_key(private_key)
            signed_txn = account.sign_transaction(transaction_data)
            return signed_txn.rawTransaction.hex()
        except Exception as e:
            raise Exception(f"Error firmando transacción: {e}")
    
    def verify_address(self, address: str) -> bool:
        """Verifica si una dirección es válida"""
        try:
            return Account.is_valid_address(address)
        except:
            return False


wallet_manager = WalletManager()


