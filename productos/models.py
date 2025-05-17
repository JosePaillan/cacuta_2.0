from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=100)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    es_casa_matriz = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Stock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stocks')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='stocks')
    cantidad = models.IntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.cantidad < 0:
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
        return f"Venta {self.id} - {self.producto.nombre}"

class CarritoCompra(models.Model):
    usuario = models.CharField(max_length=100)
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
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    fecha_agregado = models.DateTimeField(default=timezone.now)

    @property
    def subtotal(self):
        return self.stock.precio * self.cantidad

    def clean(self):
        if self.cantidad > self.stock.cantidad:
            raise ValidationError('No hay suficiente stock disponible')
        if self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0')

    def __str__(self):
        return f"{self.cantidad}x {self.stock.producto.nombre}"

    class Meta:
        unique_together = ('carrito', 'stock') 