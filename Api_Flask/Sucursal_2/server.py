import grpc
from concurrent import futures
import time
from productos_pb2 import *
from productos_pb2_grpc import add_ProductoServiceServicer_to_server, ProductoServiceServicer
from app import SessionLocal
from models import Producto
from datetime import datetime

class ProductoService(ProductoServiceServicer):
    def ListarProductos(self, request, context):
        db = SessionLocal()
        productos = db.query(Producto).all()
        for p in productos:
            yield ProductoResponse(
                id=p.id,
                nombre=p.nombre,
                descripcion=p.descripcion,
                categoria=p.categoria,
                precio_base=p.precio_base,
                fecha_creacion=p.fecha_creacion.isoformat(),
                fecha_actualizacion=p.fecha_actualizacion.isoformat()
            )

    def CrearProducto(self, request, context):
        db = SessionLocal()
        producto = Producto(
            nombre=request.nombre,
            descripcion=request.descripcion,
            categoria=request.categoria,
            precio_base=request.precio_base,
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)

        return ProductoResponse(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria=producto.categoria,
            precio_base=producto.precio_base,
            fecha_creacion=producto.fecha_creacion.isoformat(),
            fecha_actualizacion=producto.fecha_actualizacion.isoformat()
        )

    def ObtenerProducto(self, request, context):
        db = SessionLocal()
        producto = db.query(Producto).get(request.id)
        return ProductoResponse(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria=producto.categoria,
            precio_base=producto.precio_base,
            fecha_creacion=producto.fecha_creacion.isoformat(),
            fecha_actualizacion=producto.fecha_actualizacion.isoformat()
        )

    def ActualizarProducto(self, request, context):
        db = SessionLocal()
        producto = db.query(Producto).get(request.id)
        producto.nombre = request.nombre
        producto.descripcion = request.descripcion
        producto.categoria = request.categoria
        producto.precio_base = request.precio_base
        producto.fecha_actualizacion = datetime.utcnow()
        db.commit()
        return ProductoResponse(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            categoria=producto.categoria,
            precio_base=producto.precio_base,
            fecha_creacion=producto.fecha_creacion.isoformat(),
            fecha_actualizacion=producto.fecha_actualizacion.isoformat()
        )

    def EliminarProducto(self, request, context):
        db = SessionLocal()
        producto = db.query(Producto).get(request.id)
        db.delete(producto)
        db.commit()
        from google.protobuf.empty_pb2 import Empty
        return Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ProductoServiceServicer_to_server(ProductoService(), server)
    server.add_insecure_port('[::]:50053')
    print("Sucursal 2 gRPC en puerto 50053")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
