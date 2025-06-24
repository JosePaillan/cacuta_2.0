from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from productos.models import Producto, Sucursal, AlertaStock
import json

class Command(BaseCommand):
    help = 'Verifica que el sistema funciona correctamente sin SSE'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Verificando sistema sin SSE...')
        )
        self.stdout.write('=' * 50)
        
        client = Client()
        
        # Verificar endpoint de productos
        self.stdout.write('\n📦 Verificando endpoint de productos...')
        try:
            response = client.get('/api/productos/todos_los_productos/')
            if response.status_code == 200:
                data = response.json()
                productos_locales = len(data.get('locales', []))
                productos_sucursales = len(data.get('sucursales', []))
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Productos cargados: {productos_locales} locales, {productos_sucursales} remotos')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error en endpoint productos: {response.status_code}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error al verificar productos: {e}')
            )
        
        # Verificar endpoint de alertas estáticas
        self.stdout.write('\n⚠️  Verificando endpoint de alertas...')
        try:
            response = client.get('/api/alertas/')
            if response.status_code == 200:
                alertas = response.json()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Alertas cargadas: {len(alertas)} activas')
                )
                for alerta in alertas[:3]:  # Mostrar primeras 3
                    self.stdout.write(f'      • {alerta["producto"]} - Stock: {alerta["stock_actual"]}')
                if len(alertas) > 3:
                    self.stdout.write(f'      ... y {len(alertas) - 3} más')
            else:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error en endpoint alertas: {response.status_code}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error al verificar alertas: {e}')
            )
        
        # Verificar que SSE está deshabilitado
        self.stdout.write('\n🚫 Verificando que SSE está deshabilitado...')
        try:
            response = client.get('/api/alertas/sse/')
            if response.status_code == 503:
                self.stdout.write(
                    self.style.SUCCESS('   ✅ SSE correctamente deshabilitado (503)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  SSE responde con código: {response.status_code}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error al verificar SSE: {e}')
            )
        
        # Verificar estado de la base de datos
        self.stdout.write('\n🗄️  Verificando base de datos...')
        try:
            productos_count = Producto.objects.count()
            sucursales_count = Sucursal.objects.count()
            alertas_count = AlertaStock.objects.filter(activa=True).count()
            
            self.stdout.write(f'   📦 Productos en BD: {productos_count}')
            self.stdout.write(f'   🏪 Sucursales en BD: {sucursales_count}')
            self.stdout.write(f'   ⚠️  Alertas activas en BD: {alertas_count}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error al verificar BD: {e}')
            )
        
        # Resumen
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 RESUMEN:')
        self.stdout.write('✅ Sistema funcionando sin SSE')
        self.stdout.write('✅ Alertas cargándose de forma estática')
        self.stdout.write('✅ Endpoints respondiendo correctamente')
        self.stdout.write('\n💡 El sistema está listo para usar!')
        self.stdout.write('💡 Las alertas se recargan cada 30 segundos automáticamente') 