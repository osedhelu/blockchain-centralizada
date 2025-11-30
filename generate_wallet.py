#!/usr/bin/env python3
"""
Script para generar wallets Ethereum con mnemonic de 12 palabras
Uso: 
  python generate_wallet.py                    # Genera wallet en posición 0
  python generate_wallet.py --index 1          # Genera wallet en posición 1
  python generate_wallet.py --mnemonic "..."  # Importa wallet desde mnemonic
  python scripts/generate_wallet_position1.py # Script específico para posición 1
"""

import argparse
import json
from src.wallet import wallet_manager


def main():
    parser = argparse.ArgumentParser(
        description="Genera wallets Ethereum con mnemonic de 12 palabras"
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Índice de la cuenta (0 para primera wallet, 1 para segunda, etc.)"
    )
    parser.add_argument(
        "--mnemonic",
        type=str,
        default=None,
        help="Mnemonic existente para derivar wallet (opcional)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "text"],
        default="text",
        help="Formato de salida (json o text)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mnemonic:
            wallet = wallet_manager.import_wallet_from_mnemonic(
                args.mnemonic,
                account_index=args.index
            )
            print("✓ Wallet importada desde mnemonic existente")
        else:
            wallet = wallet_manager.generate_new_wallet(account_index=args.index)
            print("✓ Nueva wallet generada")
        
        if args.format == "json":
            print(json.dumps(wallet, indent=2))
        else:
            print("\n" + "="*60)
            print("WALLET GENERADA")
            print("="*60)
            print(f"\n📍 Dirección:     {wallet['address']}")
            print(f"🔑 Clave Privada:  {wallet['private_key']}")
            print(f"📝 Mnemonic:       {wallet['mnemonic']}")
            print(f"🔢 Índice:         {wallet['account_index']}")
            print(f"🛤️  Ruta:          {wallet['derivation_path']}")
            print("\n" + "="*60)
            print("⚠️  IMPORTANTE: Guarda el mnemonic y la clave privada de forma segura!")
            print("⚠️  Nunca compartas tu clave privada o mnemonic con nadie!")
            print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


