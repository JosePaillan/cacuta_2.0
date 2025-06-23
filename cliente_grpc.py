import grpc
from productos.grpc import productos_pb2, productos_pb2_grpc
from google.protobuf.empty_pb2 import Empty

# Conexión al servidor
channel = grpc.insecure_channel('localhost:50051')
stub = productos_pb2_grpc.ProductoServiceStub(channel)

# 🟢 Crear producto
nuevo = productos_pb2.ProductoCreateRequest(
    nombre="Cable HDMI 4K",
    descripcion="Cable de 2 metros, compatible 4K",
    categoria="Accesorios",
    precio_base=5990.0
)
creado = stub.CrearProducto(nuevo)
print("🔹 Producto creado:", creado)

# 🔍 Obtener producto por ID
producto = stub.ObtenerProducto(productos_pb2.ProductoRequest(id=creado.id))
print("🔍 Producto obtenido:", producto)

# 📜 Listar todos los productos
print("📜 Lista de productos:")
for p in stub.ListarProductos(Empty()):
    print("   -", p.nombre)

# ✏️ Actualizar producto
actualizado = stub.ActualizarProducto(productos_pb2.ProductoUpdateRequest(
    id=creado.id,
    nombre="Cable HDMI 8K",
    descripcion="Cable mejorado, compatible 8K",
    categoria="Accesorios Premium",
    precio_base=7990.0
))
print("✏️ Producto actualizado:", actualizado)

# ❌ Eliminar producto
stub.EliminarProducto(productos_pb2.ProductoRequest(id=creado.id))
print("❌ Producto eliminado")
