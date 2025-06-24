#!/usr/bin/env python
import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_manager.settings')
django.setup()

from productos.views import ProductoViewSet
from rest_framework.test import APIRequestFactory

def test_todos_los_productos():
    print("=== PRUEBA ENDPOINT todos_los_productos ===")
    
    # Crear una instancia del viewset
    viewset = ProductoViewSet()
    
    # Crear una request simulada
    factory = APIRequestFactory()
    request = factory.get('/api/productos/todos_los_productos/')
    
    # Llamar al método
    response = viewset.todos_los_productos(request)
    
    # Obtener los datos
    data = response.data
    
    print(f"Productos locales: {len(data['locales'])}")
    print(f"Productos de sucursales: {len(data['sucursales'])}")
    
    print("\n--- Productos Locales ---")
    for prod in data['locales']:
        print(f"  - {prod['nombre']} (ID: {prod['id']}) - {prod['nombre_sucursal']}")
    
    print("\n--- Productos de Sucursales ---")
    for prod in data['sucursales']:
        print(f"  - {prod['nombre']} (ID: {prod['id']}) - {prod['nombre_sucursal']}")
    
    print(f"\nTotal de productos: {len(data['locales']) + len(data['sucursales'])}")
    
    # Verificar si hay duplicados
    nombres_locales = [p['nombre'] for p in data['locales']]
    nombres_sucursales = [p['nombre'] for p in data['sucursales']]
    
    duplicados = set(nombres_locales) & set(nombres_sucursales)
    if duplicados:
        print(f"\n⚠️  PRODUCTOS DUPLICADOS: {duplicados}")
    else:
        print("\n✅ No hay productos duplicados")
    
    print("=== FIN PRUEBA ===")

if __name__ == "__main__":
    test_todos_los_productos() 