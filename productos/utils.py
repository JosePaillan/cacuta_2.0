import requests
from decimal import Decimal, ROUND_HALF_UP

def get_usd_rate():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/CLP')
        data = response.json()
        rate = Decimal(str(data['rates']['USD']))
        # Aseguramos que el rate tenga 6 decimales para mayor precisión
        return rate.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    except Exception as e:
        print(f"Error al obtener tipo de cambio: {e}")
        # Valor por defecto en caso de error (1 CLP ≈ 0.001200 USD)
        return Decimal('0.001200') 