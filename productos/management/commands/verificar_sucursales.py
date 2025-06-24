from django.core.management.base import BaseCommand
from productos.models import Sucursal

class Command(BaseCommand):
    help = 'Verifica y configura las sucursales con sus hosts gRPC'

    def handle(self, *args, **options):
        self.stdout.write('Verificando sucursales...')
        
        # Listar todas las sucursales
        sucursales = Sucursal.objects.all()
        
        if not sucursales.exists():
            self.stdout.write(self.style.WARNING('No hay sucursales en la base de datos'))
            return
        
        self.stdout.write(f'Encontradas {sucursales.count()} sucursales:')
        
        for sucursal in sucursales:
            self.stdout.write(f'- {sucursal.nombre}: {sucursal.host or "Sin host configurado"}')
        
        # Verificar si hay sucursales sin host
        sucursales_sin_host = sucursales.filter(host__isnull=True).exclude(es_casa_matriz=True)
        
        if sucursales_sin_host.exists():
            self.stdout.write(self.style.WARNING(f'\nSucursales sin host configurado: {sucursales_sin_host.count()}'))
            for sucursal in sucursales_sin_host:
                self.stdout.write(f'- {sucursal.nombre}')
            
            self.stdout.write('\nPara configurar los hosts, puedes usar:')
            self.stdout.write('python manage.py shell')
            self.stdout.write('>>> from productos.models import Sucursal')
            self.stdout.write('>>> sucursal = Sucursal.objects.get(nombre="Nombre de la sucursal")')
            self.stdout.write('>>> sucursal.host = "localhost:50051"  # o el puerto correspondiente')
            self.stdout.write('>>> sucursal.save()')
        else:
            self.stdout.write(self.style.SUCCESS('\nTodas las sucursales tienen host configurado')) 