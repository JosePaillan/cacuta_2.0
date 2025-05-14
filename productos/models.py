from djongo import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} - {self.codigo}"

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, default='Sin dirección')
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    es_casa_matriz = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class ProductoSucursal(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='productos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    ultima_actualizacion = models.DateTimeField(default=timezone.now)

    def clean(self):
        if self.stock < 0:
            raise ValidationError('El stock no puede ser negativo')
        if self.precio < 0:
            raise ValidationError('El precio no puede ser negativo')

    def __str__(self):
        return f"{self.producto.nombre} en {self.sucursal.nombre}"

    class Meta:
        unique_together = ('sucursal', 'producto')

class Venta(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.total:
            self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Venta {self.id} - {self.producto.nombre} en {self.sucursal.nombre}"

class CarritoCompra(models.Model):
    usuario = models.CharField(max_length=100)  # Por ahora usamos anonymous
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)
    orden_compra = models.CharField(max_length=100, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    token_ws = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f"Carrito {self.id} - {self.usuario}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(CarritoCompra, related_name='items', on_delete=models.CASCADE)
    producto_sucursal = models.ForeignKey(ProductoSucursal, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    fecha_agregado = models.DateTimeField(default=timezone.now)

    @property
    def subtotal(self):
        return self.producto_sucursal.precio * self.cantidad

    def clean(self):
        if self.cantidad > self.producto_sucursal.stock:
            raise ValidationError('No hay suficiente stock disponible')
        if self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0')

    def __str__(self):
        return f"{self.cantidad}x {self.producto_sucursal.producto.nombre} en {self.producto_sucursal.sucursal.nombre}"

    class Meta:
        unique_together = ('carrito', 'producto_sucursal') 