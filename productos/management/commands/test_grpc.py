from django.core.management.base import BaseCommand
from productos.models import Sucursal
from productos.grpc.clientes import crear_producto_en_sucursal, listar_productos_en_sucursal

class Command(BaseCommand):
    help = 'Prueba la creación y listado de productos gRPC'

    def handle(self, *args, **options):
        self.stdout.write('=== PRUEBA gRPC ===')
        
        # Listar sucursales con host
        sucursales = Sucursal.objects.exclude(host__isnull=True).exclude(host='')
        self.stdout.write(f'Sucursales disponibles: {sucursales.count()}')
        
        for sucursal in sucursales:
            self.stdout.write(f'- {sucursal.nombre}: {sucursal.host}')
        
        if not sucursales.exists():
            self.stdout.write(self.style.ERROR('No hay sucursales configuradas'))
            return
        
        # Probar con la primera sucursal
        sucursal = sucursales.first()
        self.stdout.write(f'\n--- Probando con {sucursal.nombre} ({sucursal.host}) ---')
        
        # 1. Listar productos existentes
        try:
            productos_existentes = listar_productos_en_sucursal(sucursal.host)
            self.stdout.write(f'Productos existentes: {len(productos_existentes)}')
            for prod in productos_existentes:
                self.stdout.write(f'  - {prod.nombre} (ID: {prod.id})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error listando productos: {e}'))
            return
        
        # 2. Crear un producto de prueba
        try:
            self.stdout.write('\n--- Creando producto de prueba ---')
            producto_creado = crear_producto_en_sucursal(
                nombre="Producto Test gRPC",
                descripcion="Producto de prueba para verificar funcionamiento",
                categoria="Test",
                precio_base=9999.99,
                host=sucursal.host
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Producto creado: {producto_creado.nombre} (ID: {producto_creado.id})'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creando producto: {e}'))
            return
        
        # 3. Listar productos nuevamente
        try:
            self.stdout.write('\n--- Listando productos después de crear ---')
            productos_actualizados = listar_productos_en_sucursal(sucursal.host)
            self.stdout.write(f'Productos totales: {len(productos_actualizados)}')
            for prod in productos_actualizados:
                self.stdout.write(f'  - {prod.nombre} (ID: {prod.id})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error listando productos actualizados: {e}'))
        
        self.stdout.write('\n=== PRUEBA COMPLETADA ===') 