from django.core.management.base import BaseCommand
from productos.models import Sucursal
from productos.grpc.clientes import listar_productos_en_sucursal
import grpc
from productos.grpc import productos_pb2, productos_pb2_grpc

class Command(BaseCommand):
    help = 'Agrega stock a productos de gRPC para pruebas'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Agregando stock a productos de gRPC...")
        
        # Obtener todas las sucursales con host configurado
        sucursales_con_host = Sucursal.objects.exclude(host__isnull=True).exclude(host='')
        
        for sucursal in sucursales_con_host:
            self.stdout.write(f"\n🏪 {sucursal.nombre} ({sucursal.host}):")
            
            try:
                # Conectar al servidor gRPC
                channel = grpc.insecure_channel(sucursal.host)
                stub = productos_pb2_grpc.ProductoServiceStub(channel)
                
                # Obtener productos
                productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                
                for i, prod in enumerate(productos_grpc[:3]):  # Solo los primeros 3 productos
                    stock_actual = getattr(prod, 'stock', 0)
                    
                    if stock_actual == 0:
                        # Agregar stock (10 unidades)
                        nuevo_stock = 10
                        
                        try:
                            request = productos_pb2.ProductoUpdateRequest(
                                id=prod.id,
                                nombre=prod.nombre,
                                descripcion=prod.descripcion,
                                categoria=prod.categoria,
                                precio_base=prod.precio_base,
                                stock=nuevo_stock
                            )
                            
                            response = stub.ActualizarProducto(request)
                            self.stdout.write(f"   ✅ {prod.nombre} - Stock actualizado: 0 → {nuevo_stock}")
                            
                        except Exception as e:
                            self.stdout.write(f"   ❌ Error actualizando {prod.nombre}: {str(e)}")
                    else:
                        self.stdout.write(f"   ℹ️ {prod.nombre} - Ya tiene stock: {stock_actual}")
                
            except Exception as e:
                self.stdout.write(f"   ❌ Error conectando a {sucursal.nombre}: {str(e)}")
        
        self.stdout.write("\n✅ Stock agregado a productos de gRPC!")
        self.stdout.write("💡 Ahora puedes probar el carrito con productos de gRPC") 