from django.core.management.base import BaseCommand
from django.test import RequestFactory
from productos.views import ProductoViewSet, CarritoViewSet
import json

class Command(BaseCommand):
    help = 'Prueba la vista del carrito para verificar que carga productos correctamente'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Probando vista del carrito...")
        
        # Crear una request simulada
        factory = RequestFactory()
        
        # Probar todos_los_productos
        self.stdout.write("\n📦 Probando endpoint todos_los_productos...")
        request = factory.get('/api/productos/todos_los_productos/')
        viewset = ProductoViewSet()
        viewset.request = request
        
        try:
            response = viewset.todos_los_productos(request)
            data = response.data
            
            self.stdout.write(f"✅ Productos locales: {len(data.get('locales', []))}")
            self.stdout.write(f"✅ Productos de sucursales: {len(data.get('sucursales', []))}")
            
            # Mostrar algunos productos locales
            if data.get('locales'):
                self.stdout.write("\n🏠 Productos locales disponibles:")
                for prod in data['locales'][:3]:  # Solo los primeros 3
                    self.stdout.write(f"   • {prod['nombre']} - Stock: {prod['stock']}")
            
            # Mostrar algunos productos de sucursales
            if data.get('sucursales'):
                self.stdout.write("\n🏪 Productos de sucursales disponibles:")
                for prod in data['sucursales'][:3]:  # Solo los primeros 3
                    self.stdout.write(f"   • {prod['nombre']} - Stock: {prod['stock']} ({prod['nombre_sucursal']})")
            
        except Exception as e:
            self.stdout.write(f"❌ Error en todos_los_productos: {str(e)}")
            return
        
        # Probar creación de carrito
        self.stdout.write("\n🛒 Probando creación de carrito...")
        request = factory.post('/api/carritos/', data=json.dumps({'usuario': 'test'}), content_type='application/json')
        viewset = CarritoViewSet()
        viewset.request = request
        
        try:
            response = viewset.create(request)
            carrito_data = response.data
            carrito_id = carrito_data.get('id')
            self.stdout.write(f"✅ Carrito creado con ID: {carrito_id}")
            
            # Probar agregar item local
            self.stdout.write("\n➕ Probando agregar item local...")
            if data.get('locales'):
                producto_local = data['locales'][0]
                request = factory.post(
                    f'/api/carritos/{carrito_id}/agregar_item/',
                    data=json.dumps({
                        'producto_id': producto_local['id'],
                        'sucursal_id': None,
                        'cantidad': 1
                    }),
                    content_type='application/json'
                )
                viewset.request = request
                
                try:
                    response = viewset.agregar_item(request, pk=carrito_id)
                    self.stdout.write("✅ Item local agregado correctamente")
                except Exception as e:
                    self.stdout.write(f"❌ Error agregando item local: {str(e)}")
            
            # Probar agregar item de sucursal
            self.stdout.write("\n➕ Probando agregar item de sucursal...")
            if data.get('sucursales'):
                producto_sucursal = data['sucursales'][0]
                request = factory.post(
                    f'/api/carritos/{carrito_id}/agregar_item/',
                    data=json.dumps({
                        'producto_id': producto_sucursal['id'],
                        'sucursal_id': producto_sucursal['sucursal'],
                        'cantidad': 1
                    }),
                    content_type='application/json'
                )
                viewset.request = request
                
                try:
                    response = viewset.agregar_item(request, pk=carrito_id)
                    self.stdout.write("✅ Item de sucursal agregado correctamente")
                except Exception as e:
                    self.stdout.write(f"❌ Error agregando item de sucursal: {str(e)}")
            
        except Exception as e:
            self.stdout.write(f"❌ Error en creación de carrito: {str(e)}")
        
        self.stdout.write("\n✅ Prueba completada!") 