import grpc
from concurrent import futures
from productos.grpc import productos_pb2_grpc
from productos.grpc.servicers import ProductoService

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    productos_pb2_grpc.add_ProductoServiceServicer_to_server(ProductoService(), server)
    server.add_insecure_port('[::]:50051')
    print("🟢 Servidor gRPC levantado en puerto 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
