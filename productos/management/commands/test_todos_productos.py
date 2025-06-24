from django.core.management.base import BaseCommand
from django.test import RequestFactory
from productos.views import ProductoViewSet
import json

class Command(BaseCommand):
    help = 'Prueba la función todos_los_productos para verificar que carga productos locales y de gRPC'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Probando función todos_los_productos...")
        
        # Crear una request simulada
        factory = RequestFactory()
        request = factory.get('/api/productos/todos_los_productos/')
        
        # Crear instancia del viewset
        viewset = ProductoViewSet()
        viewset.request = request
        
        try:
            # Llamar a la función
            response = viewset.todos_los_productos(request)
            
            # Obtener los datos
            data = response.data
            
            self.stdout.write("\n📊 RESULTADOS:")
            self.stdout.write(f"   Productos locales: {len(data.get('locales', []))}")
            self.stdout.write(f"   Productos de sucursales: {len(data.get('sucursales', []))}")
            
            # Mostrar productos locales
            if data.get('locales'):
                self.stdout.write("\n🏠 PRODUCTOS LOCALES:")
                for prod in data['locales']:
                    self.stdout.write(f"   • {prod['nombre']} - Stock: {prod['stock']} - ${prod['precio_base']}")
            
            # Mostrar productos de sucursales
            if data.get('sucursales'):
                self.stdout.write("\n🏪 PRODUCTOS DE SUCURSALES:")
                for prod in data['sucursales']:
                    self.stdout.write(f"   • {prod['nombre']} - Stock: {prod['stock']} - ${prod['precio_base']} ({prod['nombre_sucursal']})")
            
            self.stdout.write("\n✅ Prueba completada exitosamente!")
            
        except Exception as e:
            self.stdout.write(f"\n❌ Error en la prueba: {str(e)}")
            import traceback
            self.stdout.write(traceback.format_exc()) 