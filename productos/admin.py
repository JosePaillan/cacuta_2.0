from django.contrib import admin
from .models import Producto, Sucursal, Venta, CarritoCompra, ItemCarrito, AlertaStock

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio_base', 'stock', 'fecha_creacion']
    list_filter = ['categoria', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'direccion', 'telefono', 'email', 'host']
    list_filter = ['fecha_creacion']
    search_fields = ['nombre', 'direccion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'producto', 'cantidad', 'precio_unitario', 'total', 'es_local', 'sucursal_nombre', 'fecha_venta']
    list_filter = ['es_local', 'fecha_venta']
    search_fields = ['producto__nombre']
    readonly_fields = ['fecha_venta']

@admin.register(CarritoCompra)
class CarritoCompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha_creacion', 'completado', 'total']
    list_filter = ['completado', 'fecha_creacion']
    search_fields = ['usuario']
    readonly_fields = ['fecha_creacion']

@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ['id', 'carrito', 'nombre_producto', 'nombre_sucursal', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['fecha_agregado']
    search_fields = ['carrito__usuario']
    readonly_fields = ['fecha_agregado']

@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = ['id', 'producto', 'sucursal_nombre', 'tipo', 'stock_actual', 'umbral', 'activa', 'fecha_creacion']
    list_filter = ['tipo', 'activa', 'fecha_creacion']
    search_fields = ['producto__nombre', 'mensaje']
    readonly_fields = ['fecha_creacion'] 