from django.core.management.base import BaseCommand
from productos.models import Producto, AlertaStock, Sucursal
from productos.views import verificar_stock_bajo

class Command(BaseCommand):
    help = 'Crea múltiples alertas de stock para probar el sistema'

    def handle(self, *args, **options):
        self.stdout.write('=== CREANDO ALERTAS DE PRUEBA ===')
        
        # Crear productos con stock bajo
        productos_prueba = [
            {
                'nombre': 'Martillo Profesional',
                'descripcion': 'Martillo de alta calidad para profesionales',
                'categoria': 'Herramientas',
                'precio_base': 25000.00,
                'stock': 2
            },
            {
                'nombre': 'Destornillador Phillips',
                'descripcion': 'Destornillador Phillips de 3/8"',
                'categoria': 'Herramientas',
                'precio_base': 8500.00,
                'stock': 1
            },
            {
                'nombre': 'Taladro Eléctrico',
                'descripcion': 'Taladro eléctrico 800W con maletín',
                'categoria': 'Herramientas Eléctricas',
                'precio_base': 45000.00,
                'stock': 0
            },
            {
                'nombre': 'Pintura Interior',
                'descripcion': 'Pintura interior 4L color blanco',
                'categoria': 'Pinturas',
                'precio_base': 15000.00,
                'stock': 3
            }
        ]
        
        productos_creados = 0
        alertas_generadas = 0
        
        for datos_producto in productos_prueba:
            producto, created = Producto.objects.get_or_create(
                nombre=datos_producto['nombre'],
                defaults=datos_producto
            )
            
            if created:
                self.stdout.write(f'✅ Producto creado: {producto.nombre}')
                productos_creados += 1
            else:
                # Actualizar stock si ya existe
                producto.stock = datos_producto['stock']
                producto.save()
                self.stdout.write(f'🔄 Producto actualizado: {producto.nombre} (Stock: {producto.stock})')
            
            # Verificar si se genera alerta
            if verificar_stock_bajo(producto, producto.stock):
                alertas_generadas += 1
                self.stdout.write(f'⚠️  Alerta generada para: {producto.nombre}')
        
        # Mostrar resumen
        self.stdout.write(f'\n=== RESUMEN ===')
        self.stdout.write(f'Productos procesados: {len(productos_prueba)}')
        self.stdout.write(f'Alertas generadas: {alertas_generadas}')
        
        # Mostrar todas las alertas activas
        alertas_activas = AlertaStock.objects.filter(activa=True)
        self.stdout.write(f'\n--- Alertas Activas ({alertas_activas.count()}) ---')
        
        for alerta in alertas_activas:
            self.stdout.write(f'- {alerta.producto.nombre}: {alerta.mensaje}')
        
        self.stdout.write('\n=== PRUEBA COMPLETADA ===')
        self.stdout.write(self.style.SUCCESS('¡Ahora puedes probar el panel de alertas en el frontend!')) 