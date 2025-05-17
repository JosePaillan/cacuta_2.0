from rest_framework import serializers
from .models import Producto, Sucursal, Stock, Venta, ItemCarrito, CarritoCompra
from .utils import get_usd_rate
from decimal import Decimal

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['id', 'nombre', 'direccion', 'telefono', 'email', 'es_casa_matriz']

class StockSerializer(serializers.ModelSerializer):
    nombre_sucursal = serializers.CharField(source='sucursal.nombre', read_only=True)
    nombre_producto = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = Stock
        fields = ['id', 'sucursal', 'nombre_sucursal', 'producto', 'nombre_producto', 'precio', 'cantidad', 'ultima_actualizacion']

class ProductoSerializer(serializers.ModelSerializer):
    stocks = StockSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'categoria', 'precio_base', 
                 'stocks', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']

    def create(self, validated_data):
        return Producto.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class VentaSerializer(serializers.ModelSerializer):
    sucursal_id = serializers.IntegerField(write_only=True)
    cantidad = serializers.IntegerField()

    class Meta:
        model = Venta
        fields = ['id', 'sucursal', 'sucursal_id', 'producto', 'cantidad', 'precio_unitario', 'total', 'fecha_venta']
        read_only_fields = ['sucursal', 'precio_unitario', 'total', 'fecha_venta']

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que 0")
        return value

class ItemCarritoSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.CharField(source='stock.producto.nombre', read_only=True)
    nombre_sucursal = serializers.CharField(source='stock.sucursal.nombre', read_only=True)
    precio_unitario = serializers.DecimalField(source='stock.precio', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ['id', 'stock', 'cantidad', 'nombre_producto', 
                 'nombre_sucursal', 'precio_unitario', 'subtotal', 'fecha_agregado']
        read_only_fields = ['fecha_agregado']

class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_usd = serializers.SerializerMethodField()

    class Meta:
        model = CarritoCompra
        fields = ['id', 'usuario', 'fecha_creacion', 'completado', 'items', 'total', 'total_usd']
        read_only_fields = ['fecha_creacion', 'completado']

    def get_total_usd(self, obj):
        if not obj.total:
            return Decimal('0.00')
        usd_rate = get_usd_rate()
        total_decimal = Decimal(str(obj.total))
        return round(total_decimal * usd_rate, 2) 