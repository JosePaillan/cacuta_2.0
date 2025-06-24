import grpc
from productos.grpc import productos_pb2, productos_pb2_grpc



def crear_producto_en_sucursal(nombre, descripcion, categoria, precio_base, host, stock=0):
    channel = grpc.insecure_channel(host)
    stub = productos_pb2_grpc.ProductoServiceStub(channel)

    request = productos_pb2.ProductoCreateRequest(
        nombre=nombre,
        descripcion=descripcion,
        categoria=categoria,
        precio_base=float(precio_base),
        stock=int(stock)
    )

    return stub.CrearProducto(request)

def listar_productos_en_sucursal(host):
    channel = grpc.insecure_channel(host)
    stub = productos_pb2_grpc.ProductoServiceStub(channel)

    productos = []
    for producto in stub.ListarProductos(productos_pb2.Empty()):
        productos.append(producto)

    return productos
