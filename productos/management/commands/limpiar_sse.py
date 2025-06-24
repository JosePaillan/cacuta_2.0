from django.core.management.base import BaseCommand
from django.core.cache import cache
from productos.models import AlertaStock
import time

class Command(BaseCommand):
    help = 'Limpia conexiones SSE y reinicia el sistema de alertas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar-cache',
            action='store_true',
            help='Limpiar cache de conexiones SSE'
        )
        parser.add_argument(
            '--reset-alertas',
            action='store_true',
            help='Resetear todas las alertas activas'
        )
        parser.add_argument(
            '--todo',
            action='store_true',
            help='Ejecutar todas las operaciones de limpieza'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧹 Iniciando limpieza del sistema SSE...')
        )
        self.stdout.write('=' * 50)
        
        if options['limpiar_cache'] or options['todo']:
            self.limpiar_cache_sse()
        
        if options['reset_alertas'] or options['todo']:
            self.resetear_alertas()
        
        if not any([options['limpiar_cache'], options['reset_alertas'], options['todo']]):
            self.stdout.write('💡 Usar --todo para ejecutar todas las operaciones')
            self.stdout.write('💡 Usar --limpiar-cache para limpiar cache SSE')
            self.stdout.write('💡 Usar --reset-alertas para resetear alertas')
        
        self.mostrar_estado_actual()

    def limpiar_cache_sse(self):
        """Limpia el cache de conexiones SSE"""
        self.stdout.write('\n🗑️  Limpiando cache de conexiones SSE...')
        
        try:
            # Limpiar todo el cache
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('   ✅ Cache limpiado correctamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error al limpiar cache: {e}')
            )

    def resetear_alertas(self):
        """Resetea todas las alertas activas"""
        self.stdout.write('\n🔄 Reseteando alertas activas...')
        
        try:
            # Contar alertas activas
            alertas_activas = AlertaStock.objects.filter(activa=True).count()
            
            if alertas_activas > 0:
                # Marcar todas como inactivas
                AlertaStock.objects.filter(activa=True).update(
                    activa=False,
                    fecha_resuelta=timezone.now()
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ {alertas_activas} alertas reseteadas')
                )
            else:
                self.stdout.write('   ℹ️  No hay alertas activas para resetear')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error al resetear alertas: {e}')
            )

    def mostrar_estado_actual(self):
        """Muestra el estado actual del sistema"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 ESTADO ACTUAL DEL SISTEMA:')
        
        # Contar alertas
        alertas_activas = AlertaStock.objects.filter(activa=True).count()
        alertas_totales = AlertaStock.objects.count()
        
        self.stdout.write(f'   ⚠️  Alertas activas: {alertas_activas}')
        self.stdout.write(f'   📋 Alertas totales: {alertas_totales}')
        
        if alertas_activas > 0:
            self.stdout.write('\n🔍 Alertas activas:')
            for alerta in AlertaStock.objects.filter(activa=True)[:5]:
                self.stdout.write(f'   • {alerta.producto.nombre} - Stock: {alerta.stock_actual}')
            if alertas_activas > 5:
                self.stdout.write(f'   ... y {alertas_activas - 5} más')
        
        self.stdout.write('\n✅ Limpieza completada!')
        self.stdout.write('💡 Reinicia el servidor Django si es necesario') 