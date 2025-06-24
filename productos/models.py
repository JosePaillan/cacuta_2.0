from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=100)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.IntegerField(default=0, help_text="Stock disponible en la matriz")
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.stock < 0:
            raise ValidationError('El stock no puede ser negativo')

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"

class AlertaStock(models.Model):
    TIPO_CHOICES = [
        ('bajo', 'Stock Bajo'),
        ('agotado', 'Stock Agotado'),
        ('critico', 'Stock Crítico'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='alertas')
    sucursal_nombre = models.CharField(null=True,max_length=100, blank=True, help_text="Nombre de la sucursal gRPC (opcional)")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='bajo')
    mensaje = models.TextField()
    stock_actual = models.IntegerField()
    umbral = models.IntegerField(default=5, help_text="Umbral para considerar stock bajo")
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_resuelta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        sucursal_info = f" - {self.sucursal_nombre}" if self.sucursal_nombre else " - Local"
        return f"Alerta {self.tipo} - {self.producto.nombre}{sucursal_info}"

    class Meta:
        ordering = ['-fecha_creacion']

class Sucursal(models.Model):
    """
    Modelo simplificado solo para configurar hosts de gRPC.
    No se usa para stock local.
    """
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    host = models.CharField(max_length=200, blank=True, null=True, help_text="Host:puerto para conexión gRPC (ej: localhost:50051)")
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Venta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(default=timezone.now)
    es_local = models.BooleanField(default=True, help_text="True si es venta local, False si es de gRPC")
    sucursal_nombre = models.CharField(max_length=100, blank=True, help_text="Nombre de la sucursal gRPC (si no es local)")
    producto_id_remoto = models.IntegerField(null=True, blank=True, help_text="ID del producto en servidor gRPC")
    producto_nombre_remoto = models.CharField(max_length=200, blank=True, help_text="Nombre del producto remoto")
    producto_descripcion_remoto = models.TextField(blank=True, help_text="Descripción del producto remoto")
    producto_categoria_remoto = models.CharField(max_length=100, blank=True, help_text="Categoría del producto remoto")

    def save(self, *args, **kwargs):
        if not self.total:
            self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        if self.es_local:
            return f"Venta {self.id} - {self.producto.nombre if self.producto else 'Sin producto'} (Local)"
        else:
            return f"Venta {self.id} - {self.producto_nombre_remoto or 'Remoto'} ({self.sucursal_nombre})"

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
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True, blank=True, help_text="Producto local")
    producto_id_remoto = models.IntegerField(null=True, blank=True, help_text="ID del producto en servidor gRPC")
    sucursal_id_remoto = models.IntegerField(null=True, blank=True, help_text="ID de la sucursal gRPC")
    sucursal_nombre = models.CharField(max_length=100, blank=True, help_text="Nombre de la sucursal gRPC")
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Precio al momento de agregar al carrito")
    fecha_agregado = models.DateTimeField(default=timezone.now)

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    @property
    def es_local(self):
        return self.producto is not None

    @property
    def nombre_producto(self):
        if self.producto:
            return self.producto.nombre
        else:
            return f"Producto ID {self.producto_id_remoto}"

    @property
    def nombre_sucursal(self):
        if self.es_local:
            return "Local (Matriz)"
        else:
            return self.sucursal_nombre

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0')
        
        # Validar que sea local o remoto, no ambos
        if self.producto and (self.producto_id_remoto or self.sucursal_id_remoto):
            raise ValidationError('Un item no puede ser local y remoto al mismo tiempo')
        
        if not self.producto and not self.producto_id_remoto:
            raise ValidationError('Un item debe ser local o remoto')

    def __str__(self):
        if self.es_local:
            return f"{self.cantidad}x {self.producto.nombre} (Local)"
        else:
            return f"{self.cantidad}x Producto ID {self.producto_id_remoto} ({self.sucursal_nombre})"

    class Meta:
        unique_together = ('carrito', 'producto', 'producto_id_remoto', 'sucursal_id_remoto') 