from decimal import Decimal, ROUND_DOWN
from typing import Union


# Precisión de 18 decimales (estándar ERC-20)
DECIMALS = 18


def to_wei(amount: Union[float, str, Decimal, int]) -> int:
    """
    Convierte un monto a wei (entero sin decimales)
    Similar a cómo Ethereum maneja los tokens ERC-20
    Ejemplo: 1.5 tokens -> 1500000000000000000 (wei)
    """
    if isinstance(amount, str):
        amount = Decimal(amount)
    elif isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    elif isinstance(amount, Decimal):
        pass
    else:
        amount = Decimal(str(amount))
    
    # Multiplicar por 10^18 para convertir a wei (entero)
    multiplier = Decimal(10) ** DECIMALS
    wei = (amount * multiplier).quantize(Decimal('1'), rounding=ROUND_DOWN)
    return int(wei)


def from_wei(wei_amount: Union[int, str, Decimal]) -> Decimal:
    """
    Convierte wei (entero) a la unidad principal (dividiendo por 10^18)
    Ejemplo: 1500000000000000000 (wei) -> 1.5 tokens
    """
    if isinstance(wei_amount, str):
        wei_amount = Decimal(wei_amount)
    elif isinstance(wei_amount, int):
        wei_amount = Decimal(str(wei_amount))
    elif isinstance(wei_amount, Decimal):
        pass
    else:
        wei_amount = Decimal(str(wei_amount))
    
    divisor = Decimal(10) ** DECIMALS
    return (wei_amount / divisor).quantize(Decimal('0.' + '0' * DECIMALS), rounding=ROUND_DOWN)


def format_amount(wei_amount: Union[int, str, Decimal], decimals: int = DECIMALS) -> str:
    """
    Formatea un monto en wei (entero) a formato legible con decimales
    """
    if isinstance(wei_amount, str):
        wei_amount = Decimal(wei_amount)
    elif isinstance(wei_amount, int):
        wei_amount = Decimal(str(wei_amount))
    elif isinstance(wei_amount, Decimal):
        pass
    else:
        wei_amount = Decimal(str(wei_amount))
    
    # Convertir de wei a formato legible usando from_wei
    amount = from_wei(wei_amount)
    # Formatear eliminando ceros finales pero sin usar normalize() para evitar notación científica
    formatted = amount.quantize(Decimal('0.' + '0' * decimals), rounding=ROUND_DOWN)
    
    # Convertir a string sin notación científica
    result = str(formatted)
    # Si tiene notación científica, convertirla a formato normal
    if 'E' in result or 'e' in result:
        # Convertir notación científica a formato normal
        parts = result.split('E') if 'E' in result else result.split('e')
        base = Decimal(parts[0])
        exponent = int(parts[1])
        result = str(base * (Decimal(10) ** exponent))
    
    # Eliminar ceros finales después del punto decimal
    if '.' in result:
        result = result.rstrip('0').rstrip('.')
    
    return result


def parse_amount(amount: Union[str, float, int, Decimal]) -> int:
    """
    Parsea un monto (puede venir como decimal o entero) y lo convierte a wei (entero)
    Ejemplo: "1.5" -> 1500000000000000000
    Ejemplo: "1000000000000000000" -> 1000000000000000000 (ya está en wei)
    """
    # Si ya es un int grande (probablemente ya está en wei), retornarlo directamente
    if isinstance(amount, int):
        # Si el int es muy grande (> 10^10), asumir que ya está en wei
        if amount > 10**10:
            return amount
        # Si es un int pequeño, tratarlo como tokens y convertir a wei
        amount = Decimal(str(amount))
    elif isinstance(amount, str):
        # Si es un string muy largo sin punto, asumir que ya está en wei
        if '.' not in amount and len(amount) > 10:
            try:
                wei_int = int(amount)
                if wei_int > 10**10:
                    return wei_int
            except:
                pass
        amount = Decimal(amount)
    elif isinstance(amount, float):
        amount = Decimal(str(amount))
    elif isinstance(amount, Decimal):
        pass
    else:
        amount = Decimal(str(amount))
    
    # Convertir a wei (entero)
    return to_wei(amount)

