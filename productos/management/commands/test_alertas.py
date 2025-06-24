from django.core.management.base import BaseCommand
from productos.models import Producto, AlertaStock
from productos.views import verificar_stock_bajo

class Command(BaseCommand):
    help = 'Prueba las alertas de stock bajo'

    def handle(self, *args, **options):
        self.stdout.write('=== PRUEBA DE ALERTAS DE STOCK ===')
        
        # Crear un producto de prueba con stock bajo
        producto, created = Producto.objects.get_or_create(
            nombre="Producto Test Stock Bajo",
            defaults={
                'descripcion': 'Producto para probar alertas de stock',
                'categoria': 'Test',
                'precio_base': 1000.00,
                'stock': 3  # Stock bajo para generar alerta
            }
        )
        
        if created:
            self.stdout.write(f'✅ Producto creado: {producto.nombre}')
        else:
            self.stdout.write(f'ℹ️  Producto existente: {producto.nombre}')
        
        # Verificar si se genera alerta
        self.stdout.write(f'\n--- Verificando stock bajo ---')
        self.stdout.write(f'Stock actual: {producto.stock}')
        
        alerta_generada = verificar_stock_bajo(producto, producto.stock)
        
        if alerta_generada:
            self.stdout.write(self.style.SUCCESS('✅ Alerta generada correctamente'))
        else:
            self.stdout.write('ℹ️  No se generó alerta (posiblemente ya existe)')
        
        # Mostrar alertas activas
        alertas_activas = AlertaStock.objects.filter(activa=True)
        self.stdout.write(f'\n--- Alertas activas: {alertas_activas.count()} ---')
        
        for alerta in alertas_activas:
            self.stdout.write(f'- {alerta.producto.nombre}: {alerta.mensaje}')
        
        self.stdout.write('\n=== PRUEBA COMPLETADA ===') 