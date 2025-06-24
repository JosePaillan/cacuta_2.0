from django.core.management.base import BaseCommand
from productos.models import Sucursal
from productos.grpc.clientes import listar_productos_en_sucursal
import socket
import time

class Command(BaseCommand):
    help = 'Verifica el estado de los servidores gRPC'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=5,
            help='Timeout en segundos para la conexión (default: 5)'
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Verificando estado de servidores gRPC...')
        )
        self.stdout.write('=' * 60)
        
        # Obtener todas las sucursales
        sucursales = Sucursal.objects.all()
        
        if not sucursales.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  No hay sucursales configuradas en la base de datos')
            )
            return
        
        servidores_ok = 0
        servidores_error = 0
        
        for sucursal in sucursales:
            self.stdout.write(f"\n📡 Verificando: {sucursal.nombre}")
            self.stdout.write(f"   Host: {sucursal.host}")
            
            if not sucursal.host:
                self.stdout.write(
                    self.style.ERROR('   ❌ No hay host configurado')
                )
                servidores_error += 1
                continue
            
            # Extraer host y puerto
            try:
                if ':' in sucursal.host:
                    host, port_str = sucursal.host.split(':')
                    port = int(port_str)
                else:
                    host = sucursal.host
                    port = 50052  # Puerto por defecto
                
                # Verificar conectividad TCP
                self.stdout.write(f"   🔌 Probando conexión TCP a {host}:{port}...")
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                resultado = sock.connect_ex((host, port))
                sock.close()
                
                if resultado == 0:
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Puerto accesible')
                    )
                    
                    # Probar gRPC
                    self.stdout.write(f"   🔄 Probando gRPC...")
                    try:
                        productos = list(listar_productos_en_sucursal(host=sucursal.host))
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✅ gRPC funcionando - {len(productos)} productos')
                        )
                        servidores_ok += 1
                        
                        # Mostrar algunos productos
                        for i, prod in enumerate(productos[:3]):
                            self.stdout.write(f"      • {prod.nombre} (${prod.precio_base})")
                        if len(productos) > 3:
                            self.stdout.write(f"      ... y {len(productos) - 3} más")
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Error gRPC: {str(e)}')
                        )
                        servidores_error += 1
                        
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Puerto no accesible (código: {resultado})')
                    )
                    servidores_error += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error de conexión: {str(e)}')
                )
                servidores_error += 1
        
        # Resumen
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 RESUMEN:')
        self.stdout.write(f'   ✅ Servidores funcionando: {servidores_ok}')
        self.stdout.write(f'   ❌ Servidores con problemas: {servidores_error}')
        self.stdout.write(f'   📍 Total: {servidores_ok + servidores_error}')
        
        if servidores_error == 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Todos los servidores están funcionando correctamente!')
            )
        elif servidores_ok == 0:
            self.stdout.write(
                self.style.ERROR('\n🚨 Ningún servidor está funcionando. Ejecuta: python iniciar_servidores.py')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  {servidores_error} servidor(es) tienen problemas')
            )
            self.stdout.write('💡 Para iniciar los servidores: python iniciar_servidores.py') 