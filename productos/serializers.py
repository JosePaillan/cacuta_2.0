from rest_framework import serializers
from .models import Producto, Sucursal, ProductoSucursal, Venta, ItemCarrito, CarritoCompra

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['id', 'nombre', 'direccion', 'telefono', 'email', 'es_casa_matriz']

class ProductoSucursalSerializer(serializers.ModelSerializer):
    nombre_sucursal = serializers.CharField(source='sucursal.nombre', read_only=True)

    class Meta:
        model = ProductoSucursal
        fields = ['id', 'sucursal', 'nombre_sucursal', 'precio', 'stock', 'ultima_actualizacion']

class ProductoSerializer(serializers.ModelSerializer):
    sucursales = ProductoSucursalSerializer(many=True, read_only=True, source='productosucursal_set')

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'precio_base', 
                 'sucursales', 'fecha_creacion', 'fecha_actualizacion']
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
    nombre_producto = serializers.CharField(source='producto_sucursal.producto.nombre', read_only=True)
    nombre_sucursal = serializers.CharField(source='producto_sucursal.sucursal.nombre', read_only=True)
    precio_unitario = serializers.DecimalField(source='producto_sucursal.precio', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ['id', 'producto_sucursal', 'cantidad', 'nombre_producto', 
                 'nombre_sucursal', 'precio_unitario', 'subtotal', 'fecha_agregado']
        read_only_fields = ['fecha_agregado']

class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CarritoCompra
        fields = ['id', 'usuario', 'fecha_creacion', 'completado', 'items', 'total']
        read_only_fields = ['fecha_creacion', 'completado'] 