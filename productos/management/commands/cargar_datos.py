from django.core.management.base import BaseCommand
from productos.models import Producto, Sucursal, Stock
import random

class Command(BaseCommand):
    help = 'Carga datos iniciales de productos y sucursales'

    def handle(self, *args, **kwargs):
        # Crear sucursales
        sucursales = [
            {'nombre': 'Casa Matriz Central', 'direccion': 'Av. Principal 123'},
            {'nombre': 'Sucursal Norte', 'direccion': 'Calle Norte 456'},
            {'nombre': 'Sucursal Sur', 'direccion': 'Av. Sur 789'},
            {'nombre': 'Casa Matriz Este', 'direccion': 'Boulevard Este 321'},
            {'nombre': 'Sucursal Oeste', 'direccion': 'Calle Oeste 654'}
        ]

        for sucursal_data in sucursales:
            Sucursal.objects.get_or_create(
                nombre=sucursal_data['nombre'],
                direccion=sucursal_data['direccion']
            )

        # Definir categorías y productos
        productos = {
            'Herramientas Manuales': [
                'Martillo de Carpintero',
                'Martillo de Goma',
                'Destornillador Phillips',
                'Destornillador Plano',
                'Llave Inglesa Ajustable',
                'Set de Llaves Allen',
                'Llave de Tubo'
            ],
            'Herramientas Eléctricas': [
                'Taladro Percutor 800W',
                'Taladro Inalámbrico 20V',
                'Sierra Circular 1200W',
                'Sierra Caladora 600W',
                'Lijadora Orbital',
                'Lijadora de Banda'
            ],
            'Materiales de Construcción': [
                'Cemento Portland 50kg',
                'Arena Fina m³',
                'Ladrillos Cerámicos x1000',
                'Pintura Látex 20L',
                'Barniz Marino 4L',
                'Cerámica 45x45 Caja',
                'Porcelanato 60x60 Caja'
            ],
            'Equipos de Seguridad': [
                'Casco de Seguridad',
                'Guantes de Cuero',
                'Guantes de Nitrilo',
                'Lentes de Seguridad',
                'Protector Auditivo',
                'Mascarilla N95'
            ],
            'Accesorios Varios': [
                'Tornillos 1" x100',
                'Tornillos 2" x100',
                'Anclajes Plásticos x50',
                'Adhesivo Construcción 1kg',
                'Silicona Transparente',
                'Cinta Adhesiva Doble Faz'
            ]
        }

        # Crear productos y stock
        sucursales_obj = list(Sucursal.objects.all())

        for categoria, productos_list in productos.items():
            for producto_nombre in productos_list:
                # Crear producto
                precio_base = random.randint(5000, 500000)  # Precio base entre 5.000 y 500.000
                producto, created = Producto.objects.get_or_create(
                    nombre=producto_nombre,
                    categoria=categoria,
                    defaults={
                        'descripcion': f'Descripción detallada de {producto_nombre}',
                        'precio_base': precio_base
                    }
                )

                # Crear stock para cada sucursal
                for sucursal in sucursales_obj:
                    # Variar precio por sucursal (±10% del precio base)
                    variacion = random.uniform(0.9, 1.1)
                    precio_sucursal = int(precio_base * variacion)
                    
                    # Stock aleatorio entre 10 y 100
                    cantidad = random.randint(10, 100)
                    
                    Stock.objects.get_or_create(
                        producto=producto,
                        sucursal=sucursal,
                        defaults={
                            'cantidad': cantidad,
                            'precio': precio_sucursal
                        }
                    )

        self.stdout.write(self.style.SUCCESS('Datos cargados exitosamente')) 