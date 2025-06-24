from django.core.management.base import BaseCommand
from django.utils import timezone
from productos.models import Producto, Sucursal, AlertaStock
from productos.grpc.clientes import crear_producto_en_sucursal
import random

class Command(BaseCommand):
    help = 'Prueba el sistema completo: crea productos, alertas y verifica funcionalidad'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crear-productos',
            action='store_true',
            help='Crear productos de prueba en todas las sucursales'
        )
        parser.add_argument(
            '--crear-alertas',
            action='store_true',
            help='Crear alertas de stock de prueba'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpiar datos de prueba'
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            self.limpiar_datos_prueba()
            return

        self.stdout.write(
            self.style.SUCCESS('🧪 Iniciando pruebas del sistema completo...')
        )
        self.stdout.write('=' * 60)

        # Verificar sucursales
        sucursales = Sucursal.objects.all()
        if not sucursales.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay sucursales configuradas')
            )
            return

        self.stdout.write(f'📍 Sucursales encontradas: {sucursales.count()}')
        for sucursal in sucursales:
            self.stdout.write(f'   • {sucursal.nombre} ({sucursal.host})')

        # Crear productos si se solicita
        if options['crear_productos']:
            self.crear_productos_prueba()

        # Crear alertas si se solicita
        if options['crear_alertas']:
            self.crear_alertas_prueba()

        # Mostrar resumen
        self.mostrar_resumen()

    def crear_productos_prueba(self):
        """Crea productos de prueba en todas las sucursales"""
        self.stdout.write('\n🛍️  Creando productos de prueba...')
        
        productos_prueba = [
            {
                'nombre': 'Laptop Gaming Pro',
                'descripcion': 'Laptop de alto rendimiento para gaming',
                'categoria': 'Electrónicos',
                'precio_base': 1200000
            },
            {
                'nombre': 'Smartphone Galaxy S23',
                'descripcion': 'Teléfono inteligente de última generación',
                'categoria': 'Electrónicos',
                'precio_base': 800000
            },
            {
                'nombre': 'Auriculares Bluetooth',
                'descripcion': 'Auriculares inalámbricos con cancelación de ruido',
                'categoria': 'Accesorios',
                'precio_base': 150000
            },
            {
                'nombre': 'Mouse Gaming RGB',
                'descripcion': 'Mouse para gaming con iluminación RGB',
                'categoria': 'Accesorios',
                'precio_base': 80000
            },
            {
                'nombre': 'Teclado Mecánico',
                'descripcion': 'Teclado mecánico con switches Cherry MX',
                'categoria': 'Accesorios',
                'precio_base': 120000
            }
        ]

        sucursales = Sucursal.objects.exclude(host__isnull=True).exclude(host='')
        
        for i, producto_data in enumerate(productos_prueba):
            self.stdout.write(f'\n📦 Creando producto {i+1}/{len(productos_prueba)}: {producto_data["nombre"]}')
            
            # Crear producto local
            producto_local, created = Producto.objects.get_or_create(
                nombre=producto_data['nombre'],
                defaults={
                    'descripcion': producto_data['descripcion'],
                    'categoria': producto_data['categoria'],
                    'precio_base': producto_data['precio_base'],
                    'stock': random.randint(1, 50)  # Stock aleatorio
                }
            )
            
            if created:
                self.stdout.write(f'   ✅ Producto local creado (ID: {producto_local.id})')
            else:
                self.stdout.write(f'   ℹ️  Producto local ya existía (ID: {producto_local.id})')

            # Crear en sucursales gRPC
            for sucursal in sucursales:
                try:
                    self.stdout.write(f'   🔄 Creando en {sucursal.nombre}...')
                    producto_grpc = crear_producto_en_sucursal(
                        host=sucursal.host,
                        nombre=producto_data['nombre'],
                        descripcion=producto_data['descripcion'],
                        categoria=producto_data['categoria'],
                        precio_base=producto_data['precio_base'],
                        stock=random.randint(1, 50)  # Stock aleatorio para cada sucursal
                    )
                    self.stdout.write(f'   ✅ Creado en {sucursal.nombre} (ID: {producto_grpc.id}, Stock: {producto_grpc.stock})')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Error en {sucursal.nombre}: {str(e)}')
                    )

    def crear_alertas_prueba(self):
        """Crea alertas de stock de prueba"""
        self.stdout.write('\n⚠️  Creando alertas de stock de prueba...')
        
        # Obtener productos con stock bajo
        productos_bajo_stock = Producto.objects.filter(stock__lte=5)
        
        if not productos_bajo_stock.exists():
            self.stdout.write('   ℹ️  No hay productos con stock bajo para crear alertas')
            return

        alertas_creadas = 0
        for producto in productos_bajo_stock:
            # Verificar si ya existe una alerta activa
            alerta_existente = AlertaStock.objects.filter(
                producto=producto,
                activa=True
            ).first()
            
            if not alerta_existente:
                mensaje = f"⚠️ Stock bajo en Local: {producto.nombre} (Stock: {producto.stock}, Umbral: 5)"
                
                AlertaStock.objects.create(
                    producto=producto,
                    sucursal=None,  # Local
                    tipo='bajo',
                    mensaje=mensaje,
                    stock_actual=producto.stock,
                    umbral=5
                )
                
                self.stdout.write(f'   ✅ Alerta creada para {producto.nombre} (Stock: {producto.stock})')
                alertas_creadas += 1
            else:
                self.stdout.write(f'   ℹ️  Alerta ya existe para {producto.nombre}')

        self.stdout.write(f'\n📊 Alertas creadas: {alertas_creadas}')

    def mostrar_resumen(self):
        """Muestra un resumen del estado del sistema"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 RESUMEN DEL SISTEMA:')
        
        # Productos
        productos_locales = Producto.objects.count()
        self.stdout.write(f'   📦 Productos locales: {productos_locales}')
        
        # Sucursales
        sucursales = Sucursal.objects.count()
        self.stdout.write(f'   🏪 Sucursales: {sucursales}')
        
        # Alertas activas
        alertas_activas = AlertaStock.objects.filter(activa=True).count()
        self.stdout.write(f'   ⚠️  Alertas activas: {alertas_activas}')
        
        if alertas_activas > 0:
            self.stdout.write('\n🔍 Alertas activas:')
            for alerta in AlertaStock.objects.filter(activa=True):
                self.stdout.write(f'   • {alerta.producto.nombre} - Stock: {alerta.stock_actual}')
        
        self.stdout.write('\n✅ Pruebas completadas!')
        self.stdout.write('💡 Para verificar servidores: python manage.py verificar_servidores')
        self.stdout.write('💡 Para iniciar servidores: python iniciar_servidores.py')

    def limpiar_datos_prueba(self):
        """Limpia los datos de prueba"""
        self.stdout.write('🧹 Limpiando datos de prueba...')
        
        # Limpiar alertas
        alertas_eliminadas = AlertaStock.objects.filter(activa=True).count()
        AlertaStock.objects.filter(activa=True).delete()
        self.stdout.write(f'   🗑️  Alertas eliminadas: {alertas_eliminadas}')
        
        # Limpiar productos de prueba
        productos_eliminados = Producto.objects.filter(
            nombre__in=[
                'Laptop Gaming Pro',
                'Smartphone Galaxy S23',
                'Auriculares Bluetooth',
                'Mouse Gaming RGB',
                'Teclado Mecánico'
            ]
        ).count()
        Producto.objects.filter(
            nombre__in=[
                'Laptop Gaming Pro',
                'Smartphone Galaxy S23',
                'Auriculares Bluetooth',
                'Mouse Gaming RGB',
                'Teclado Mecánico'
            ]
        ).delete()
        self.stdout.write(f'   🗑️  Productos de prueba eliminados: {productos_eliminados}')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Datos de prueba limpiados correctamente!')
        ) 