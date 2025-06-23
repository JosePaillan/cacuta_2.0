from productos.models import Producto
from productos.grpc import productos_pb2, productos_pb2_grpc
from google.protobuf.empty_pb2 import Empty
from django.utils.timezone import localtime

class ProductoService(productos_pb2_grpc.ProductoServiceServicer):

    def ListarProductos(self, request, context):
        for producto in Producto.objects.all():
            yield productos_pb2.ProductoResponse(
                id=producto.id,
                nombre=producto.nombre,
                descripcion=producto.descripcion,
                categoria=producto.categoria,
                precio_base=float(producto.precio_base),
                fecha_creacion=str(localtime(producto.fecha_creacion)),
                fecha_actualizacion=str(localtime(producto.fecha_actualizacion)),
            )

    def ObtenerProducto(self, request, context):
        producto = Producto.objects.get(pk=request.id)
        return productos_pb2.ProductoResponse(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria=producto.categoria,
            precio_base=float(producto.precio_base),
            fecha_creacion=str(localtime(producto.fecha_creacion)),
            fecha_actualizacion=str(localtime(producto.fecha_actualizacion)),
        )

    def CrearProducto(self, request, context):
        producto = Producto.objects.create(
            nombre=request.nombre,
            descripcion=request.descripcion,
            categoria=request.categoria,
            precio_base=request.precio_base,
        )
        return productos_pb2.ProductoResponse(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria=producto.categoria,
            precio_base=float(producto.precio_base),
            fecha_creacion=str(localtime(producto.fecha_creacion)),
            fecha_actualizacion=str(localtime(producto.fecha_actualizacion)),
        )

    def ActualizarProducto(self, request, context):
        producto = Producto.objects.get(pk=request.id)
        producto.nombre = request.nombre
        producto.descripcion = request.descripcion
        producto.categoria = request.categoria
        producto.precio_base = request.precio_base
        producto.save()
        return productos_pb2.ProductoResponse(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria=producto.categoria,
            precio_base=float(producto.precio_base),
            fecha_creacion=str(localtime(producto.fecha_creacion)),
            fecha_actualizacion=str(localtime(producto.fecha_actualizacion)),
        )

    def EliminarProducto(self, request, context):
        Producto.objects.filter(pk=request.id).delete()
        return Empty()
