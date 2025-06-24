from django.core.management.base import BaseCommand
from productos.models import Producto, Stock

class Command(BaseCommand):
    help = 'Limpia productos duplicados de Django que existen en las sucursales gRPC'

    def handle(self, *args, **options):
        self.stdout.write('=== LIMPIANDO PRODUCTOS DUPLICADOS ===')
        
        # Lista de productos que sabemos que existen en las sucursales gRPC
        productos_grpc = [
            'Destornillador eléctrico',
            'Carro', 
            'sadads',
            'martillo',
            'PPP',
            'Producto Test gRPC'
        ]
        
        productos_eliminados = 0
        
        for nombre_producto in productos_grpc:
            try:
                productos = Producto.objects.filter(nombre=nombre_producto)
                if productos.exists():
                    count = productos.count()
                    productos.delete()
                    self.stdout.write(f'✅ Eliminados {count} productos: "{nombre_producto}"')
                    productos_eliminados += count
                else:
                    self.stdout.write(f'ℹ️  No se encontraron productos: "{nombre_producto}"')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error eliminando "{nombre_producto}": {e}'))
        
        # También limpiar stocks huérfanos
        stocks_eliminados = 0
        for stock in Stock.objects.all():
            if not Producto.objects.filter(id=stock.producto.id).exists():
                stock.delete()
                stocks_eliminados += 1
        
        self.stdout.write(f'\n=== RESUMEN ===')
        self.stdout.write(f'Productos eliminados: {productos_eliminados}')
        self.stdout.write(f'Stocks huérfanos eliminados: {stocks_eliminados}')
        
        # Verificar estado final
        productos_restantes = Producto.objects.count()
        self.stdout.write(f'Productos restantes en Django: {productos_restantes}')
        
        if productos_restantes == 0:
            self.stdout.write(self.style.SUCCESS('✅ Django está completamente limpio'))
        else:
            self.stdout.write(f'Productos restantes:')
            for prod in Producto.objects.all():
                self.stdout.write(f'  - {prod.nombre} (ID: {prod.id})')
        
        self.stdout.write('=== LIMPIEZA COMPLETADA ===') 