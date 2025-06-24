from django.core.management.base import BaseCommand
from productos.models import Sucursal
from productos.grpc.clientes import listar_productos_en_sucursal

class Command(BaseCommand):
    help = 'Verifica el stock de productos en los servidores gRPC'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando stock en servidores gRPC...")
        
        # Obtener todas las sucursales con host configurado
        sucursales_con_host = Sucursal.objects.exclude(host__isnull=True).exclude(host='')
        
        for sucursal in sucursales_con_host:
            self.stdout.write(f"\n🏪 {sucursal.nombre} ({sucursal.host}):")
            
            try:
                productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                
                productos_con_stock = 0
                productos_sin_stock = 0
                
                for prod in productos_grpc:
                    stock_actual = getattr(prod, 'stock', 0)
                    if stock_actual > 0:
                        productos_con_stock += 1
                        self.stdout.write(f"   ✅ {prod.nombre} - Stock: {stock_actual}")
                    else:
                        productos_sin_stock += 1
                        self.stdout.write(f"   ❌ {prod.nombre} - Stock: {stock_actual}")
                
                self.stdout.write(f"\n   📊 Resumen: {productos_con_stock} con stock, {productos_sin_stock} sin stock")
                
            except Exception as e:
                self.stdout.write(f"   ❌ Error: {str(e)}")
        
        self.stdout.write("\n💡 Para agregar stock a productos de gRPC, usa:")
        self.stdout.write("   python manage.py crear_datos_prueba")
        self.stdout.write("   O actualiza manualmente el stock en los servidores gRPC") 