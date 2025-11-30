#!/usr/bin/env python3
"""
Script específico para generar wallet en posición 1 (índice 1)
Uso: python scripts/generate_wallet_position1.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.wallet import wallet_manager
import json


def main():
    print("\n" + "="*70)
    print("GENERADOR DE WALLET EN POSICIÓN 1")
    print("="*70)
    
    try:
        # Generar wallet en posición 1 (account_index = 1)
        wallet = wallet_manager.generate_new_wallet(account_index=1)
        
        print("\n✓ Wallet generada exitosamente en posición 1")
        print("\n" + "-"*70)
        print("INFORMACIÓN DE LA WALLET")
        print("-"*70)
        print(f"\n📍 Dirección:     {wallet['address']}")
        print(f"🔑 Clave Privada:  {wallet['private_key']}")
        print(f"📝 Mnemonic (12 palabras):")
        print(f"   {wallet['mnemonic']}")
        print(f"\n🔢 Índice de Cuenta: {wallet['account_index']}")
        print(f"🛤️  Ruta de Derivación: {wallet['derivation_path']}")
        print("\n" + "="*70)
        print("⚠️  ADVERTENCIAS DE SEGURIDAD")
        print("="*70)
        print("⚠️  Guarda el mnemonic de forma SEGURA y PRIVADA")
        print("⚠️  Nunca compartas tu clave privada o mnemonic con nadie")
        print("⚠️  Quien tenga acceso al mnemonic puede controlar tu wallet")
        print("⚠️  Haz una copia de seguridad en un lugar seguro")
        print("="*70 + "\n")
        
        # Opcional: guardar en archivo JSON (comentado por seguridad)
        # save_option = input("¿Deseas guardar la wallet en un archivo JSON? (s/N): ")
        # if save_option.lower() == 's':
        #     filename = f"wallet_position1_{wallet['address'][:10]}.json"
        #     with open(filename, 'w') as f:
        #         json.dump(wallet, f, indent=2)
        #     print(f"✓ Wallet guardada en {filename}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error generando wallet: {e}")
        print("\nPosibles soluciones:")
        print("1. Verifica que todas las dependencias estén instaladas")
        print("2. Asegúrate de tener hdwallet instalado: pip install hdwallet")
        print("3. Revisa que el mnemonic sea válido si estás importando uno")
        return 1


if __name__ == "__main__":
    exit(main())

