#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_manager.settings')
django.setup()

from productos.models import Sucursal

def configurar_hosts():
    print("Configurando hosts de sucursales gRPC...")
    
    # Configurar cada sucursal con su puerto correspondiente
    configuraciones = {
        "Sucursal Norte": "localhost:50052",
        "Sucursal Sur": "localhost:50053", 
        "Sucursal Oeste": "localhost:50054"
    }
    
    for nombre_sucursal, host in configuraciones.items():
        try:
            sucursal = Sucursal.objects.get(nombre=nombre_sucursal)
            sucursal.host = host
            sucursal.save()
            print(f"✅ {nombre_sucursal} configurada con host: {host}")
        except Sucursal.DoesNotExist:
            print(f"❌ Sucursal '{nombre_sucursal}' no encontrada")
        except Exception as e:
            print(f"❌ Error configurando {nombre_sucursal}: {e}")
    
    print("\nVerificando configuración final:")
    for sucursal in Sucursal.objects.all():
        print(f"- {sucursal.nombre}: {sucursal.host or 'Sin host'}")
    
    print("\n¡Configuración completada!")

if __name__ == "__main__":
    configurar_hosts() 