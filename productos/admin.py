from django.contrib import admin
from .models import Producto, Sucursal, Stock, Venta, CarritoCompra, ItemCarrito

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base')
    search_fields = ('nombre', 'categoria')
    list_filter = ('categoria',)

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'es_casa_matriz')
    search_fields = ('nombre', 'direccion')
    list_filter = ('es_casa_matriz',)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'sucursal', 'cantidad', 'precio')
    search_fields = ('producto__nombre', 'sucursal__nombre')
    list_filter = ('sucursal',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'sucursal', 'cantidad', 'total', 'fecha_venta')
    search_fields = ('producto__nombre', 'sucursal__nombre')
    list_filter = ('sucursal', 'fecha_venta')

@admin.register(CarritoCompra)
class CarritoCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'completado', 'fecha_creacion')
    list_filter = ('completado',)

@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ('carrito', 'stock', 'cantidad', 'subtotal')
    search_fields = ('stock__producto__nombre',) 