from rest_framework import serializers
from .models import Producto, Sucursal, Venta, ItemCarrito, CarritoCompra
from .utils import get_usd_rate
from decimal import Decimal

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['id', 'nombre', 'direccion', 'telefono', 'email', 'host']

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'categoria', 'precio_base', 
                 'stock', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']

    def create(self, validated_data):
        return Producto.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = ['id', 'producto', 'cantidad', 'precio_unitario', 'total', 
                 'fecha_venta', 'es_local', 'sucursal_nombre']
        read_only_fields = ['precio_unitario', 'total', 'fecha_venta']

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que 0")
        return value

class ItemCarritoSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.SerializerMethodField()
    nombre_sucursal = serializers.SerializerMethodField()
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ['id', 'producto', 'producto_id_remoto', 'sucursal_id_remoto', 
                 'sucursal_nombre', 'cantidad', 'nombre_producto', 
                 'nombre_sucursal', 'precio_unitario', 'subtotal', 'fecha_agregado']
        read_only_fields = ['fecha_agregado']
    
    def get_nombre_producto(self, obj):
        return obj.nombre_producto
    
    def get_nombre_sucursal(self, obj):
        return obj.nombre_sucursal

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