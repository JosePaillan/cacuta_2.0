from django.core.management.base import BaseCommand
from productos.models import Sucursal, Producto, ProductoSucursal
from decimal import Decimal

class Command(BaseCommand):
    help = 'Crea datos de prueba para la aplicación'

    def handle(self, *args, **kwargs):
        # Crear sucursales
        self.stdout.write('Creando sucursales...')
        casa_matriz = Sucursal.objects.create(
            nombre='Casa Matriz',
            direccion='Av. Principal 123',
            telefono='912345678',
            email='matriz@ejemplo.com',
            es_casa_matriz=True
        )

        sucursal_1 = Sucursal.objects.create(
            nombre='Sucursal Centro',
            direccion='Plaza Central 456',
            telefono='923456789',
            email='centro@ejemplo.com',
            es_casa_matriz=False
        )

        # Crear productos
        self.stdout.write('Creando productos...')
        productos = [
            Producto.objects.create(
                nombre='Laptop HP',
                codigo='LAP001',
                descripcion='Laptop HP 15.6" Core i5',
                precio_base=Decimal('799999.99')
            ),
            Producto.objects.create(
                nombre='Monitor LG',
                codigo='MON001',
                descripcion='Monitor LG 24" Full HD',
                precio_base=Decimal('149999.99')
            ),
            Producto.objects.create(
                nombre='Teclado Mecánico',
                codigo='TEC001',
                descripcion='Teclado Mecánico RGB',
                precio_base=Decimal('49999.99')
            )
        ]

        # Asignar productos a sucursales
        self.stdout.write('Asignando productos a sucursales...')
        for producto in productos:
            # Stock en casa matriz
            ProductoSucursal.objects.create(
                sucursal=casa_matriz,
                producto=producto,
                precio=producto.precio_base,
                stock=100
            )
            # Stock en sucursal centro (con precio ligeramente mayor)
            ProductoSucursal.objects.create(
                sucursal=sucursal_1,
                producto=producto,
                precio=producto.precio_base * Decimal('1.1'),  # 10% más caro
                stock=50
            )

        self.stdout.write(self.style.SUCCESS('Datos de prueba creados exitosamente')) 