from django.core.management.base import BaseCommand
from productos.models import ItemCarrito
from decimal import Decimal, InvalidOperation

class Command(BaseCommand):
    help = 'Limpia o corrige los ItemCarrito con precio_unitario inválido (None, NaN, string vacío, etc.)'

    def handle(self, *args, **options):
        self.stdout.write('Buscando items de carrito con precio_unitario inválido...')
        items = ItemCarrito.objects.all()
        corregidos = 0
        eliminados = 0
        for item in items:
            try:
                # Si es None, string vacío, NaN, o no convertible
                if item.precio_unitario is None or str(item.precio_unitario).strip() == '' or str(item.precio_unitario).lower() == 'nan':
                    raise InvalidOperation('Valor nulo o NaN')
                # Intentar convertir a Decimal
                _ = Decimal(item.precio_unitario)
            except Exception:
                # Intentar corregir
                try:
                    item.precio_unitario = Decimal('0.00')
                    item.save()
                    corregidos += 1
                    self.stdout.write(f'Corregido item {item.id} (carrito {item.carrito_id})')
                except Exception:
                    item.delete()
                    eliminados += 1
                    self.stdout.write(f'Eliminado item {item.id} (carrito {item.carrito_id})')
        self.stdout.write(f'Proceso terminado. Corregidos: {corregidos}, Eliminados: {eliminados}') 