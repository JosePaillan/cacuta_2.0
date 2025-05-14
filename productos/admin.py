from django.contrib import admin
from .models import Producto, Sucursal, ProductoSucursal, Venta

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email', 'es_casa_matriz')
    search_fields = ('nombre', 'direccion')
    list_filter = ('es_casa_matriz',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'precio_base', 'fecha_actualizacion')
    search_fields = ('nombre', 'codigo')
    list_filter = ('fecha_creacion',)

@admin.register(ProductoSucursal)
class ProductoSucursalAdmin(admin.ModelAdmin):
    list_display = ('sucursal', 'producto', 'precio', 'stock', 'ultima_actualizacion')
    list_filter = ('sucursal', 'producto')
    search_fields = ('producto__nombre', 'producto__codigo', 'sucursal__nombre')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('sucursal', 'producto', 'cantidad', 'precio_unitario', 'total', 'fecha_venta')
    list_filter = ('sucursal', 'producto', 'fecha_venta')
    search_fields = ('producto__nombre', 'sucursal__nombre') 