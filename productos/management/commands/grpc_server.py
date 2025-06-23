from django.core.management.base import BaseCommand
from productos.grpc.server import serve

class Command(BaseCommand):
    help = 'Inicia el servidor gRPC para productos'

    def handle(self, *args, **kwargs):
        serve()
