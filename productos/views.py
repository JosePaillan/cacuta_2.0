from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import transaction
from django.core.exceptions import ValidationError
import requests
from decimal import Decimal
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Producto, Sucursal, Stock, CarritoCompra, ItemCarrito, Venta
from .serializers import ProductoSerializer, VentaSerializer, SucursalSerializer, StockSerializer, CarritoSerializer, ItemCarritoSerializer

# Configuración de Transbank para ambiente de integración
webpay_options = WebpayOptions(
    commerce_code="597055555532",
    api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
    integration_type=IntegrationType.TEST
)
tx = Transaction(options=webpay_options)

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def get_queryset(self):
        queryset = Producto.objects.all()
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        return queryset

    @action(detail=True, methods=['get'])
    def stock_sucursal(self, request, pk=None):
        producto = self.get_object()
        sucursal_id = request.query_params.get('sucursal_id', None)
        
        if not sucursal_id:
            return Response(
                {"error": "Debe especificar una sucursal"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stock = Stock.objects.get(
                producto=producto,
                sucursal_id=sucursal_id
            )
            serializer = StockSerializer(stock)
            return Response(serializer.data)
        except Stock.DoesNotExist:
            return Response(
                {"error": "Sucursal no encontrada para este producto"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def realizar_venta(self, request, pk=None):
        producto = self.get_object()
        serializer = VentaSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                stock = Stock.objects.get(
                    producto=producto,
                    sucursal_id=serializer.validated_data['sucursal_id']
                )

                cantidad = serializer.validated_data['cantidad']

                # Verificar stock
                if stock.cantidad < cantidad:
                    return Response(
                        {"error": "Stock insuficiente"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Crear la venta
                venta = Venta.objects.create(
                    sucursal=stock.sucursal,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=stock.precio,
                    total=stock.precio * cantidad
                )

                # Actualizar stock
                stock.cantidad -= cantidad
                stock.save()

                # Notificar si el stock es bajo
                if stock.cantidad <= 5:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "stock_notifications",
                        {
                            "type": "stock_notification",
                            "message": f"¡Alerta! Stock bajo ({stock.cantidad} unidades) en {stock.sucursal.nombre} para {producto.nombre}"
                        }
                    )

                return Response({
                    "mensaje": "Venta realizada con éxito",
                    "venta_id": venta.id,
                    "nuevo_stock": stock.cantidad
                })
        except Stock.DoesNotExist:
            return Response(
                {"error": "Sucursal no encontrada para este producto"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def precio_usd(self, request, pk=None):
        producto = self.get_object()
        sucursal_id = request.query_params.get('sucursal_id', None)
        
        # Mock de API de tipo de cambio (en producción usar API real)
        tipo_cambio = Decimal('850')  # 1 USD = 850 CLP (ejemplo)
        
        if sucursal_id:
            try:
                stock = Stock.objects.get(
                    producto=producto,
                    sucursal_id=sucursal_id
                )
                precio_usd = Decimal(str(stock.precio)) / tipo_cambio
                return Response({
                    "precio_usd": round(precio_usd, 2)
                })
            except Stock.DoesNotExist:
                return Response(
                    {"error": "Sucursal no encontrada para este producto"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            precio_usd = producto.precio_base / tipo_cambio
            return Response({
                "precio_usd": round(precio_usd, 2)
            })

    @action(detail=True, methods=['post'])
    def actualizar_stock(self, request, pk=None):
        try:
            producto = self.get_object()
            sucursal_id = request.data.get('sucursal_id')
            nueva_cantidad = request.data.get('cantidad')
            
            if nueva_cantidad is None:
                return Response({'error': 'Debe proporcionar la nueva cantidad'}, status=400)
            
            if sucursal_id is None:
                return Response({'error': 'Debe proporcionar el ID de la sucursal'}, status=400)
            
            try:
                stock = Stock.objects.get(
                    producto=producto,
                    sucursal_id=sucursal_id
                )
            except Stock.DoesNotExist:
                return Response({'error': 'No se encontró el producto en la sucursal especificada'}, status=404)
            
            stock.cantidad = nueva_cantidad
            stock.save()

            # Notificar si el stock es bajo (menor o igual a 5)
            if stock.cantidad <= 5:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "stock_notifications",
                    {
                        "type": "stock_notification",
                        "message": f"¡Alerta! Stock bajo ({stock.cantidad} unidades) en {stock.sucursal.nombre} para {stock.producto.nombre}"
                    }
                )

            return Response({'cantidad': stock.cantidad})
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class SucursalViewSet(viewsets.ModelViewSet):
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer

class CarritoViewSet(viewsets.ModelViewSet):
    queryset = CarritoCompra.objects.all()
    serializer_class = CarritoSerializer

    def create(self, request, *args, **kwargs):
        # Buscar un carrito no completado existente
        carrito = CarritoCompra.objects.filter(
            usuario=request.data.get('usuario', 'anonymous'),
            completado=False
        ).first()

        if carrito:
            serializer = self.get_serializer(carrito)
            return Response(serializer.data)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def agregar_item(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "No se puede modificar un carrito completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        producto_id = request.data.get('producto_id')
        sucursal_id = request.data.get('sucursal_id')
        cantidad = int(request.data.get('cantidad', 1))

        try:
            stock = Stock.objects.get(
                producto_id=producto_id,
                sucursal_id=sucursal_id
            )

            if stock.cantidad < cantidad:
                return Response(
                    {"error": "Stock insuficiente"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item, created = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                stock=stock,
                defaults={'cantidad': cantidad}
            )

            if not created:
                item.cantidad += cantidad
                if item.cantidad > stock.cantidad:
                    return Response(
                        {"error": "Stock insuficiente"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                item.save()

            serializer = CarritoSerializer(carrito)
            return Response(serializer.data)

        except Stock.DoesNotExist:
            return Response(
                {"error": "Producto no encontrado en la sucursal especificada"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def actualizar_item(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "No se puede modificar un carrito completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        item_id = request.data.get('item_id')
        cantidad = request.data.get('cantidad')

        try:
            item = ItemCarrito.objects.get(id=item_id, carrito=carrito)
            if cantidad > item.stock.cantidad:
                return Response(
                    {"error": "Stock insuficiente"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item.cantidad = cantidad
            item.save()

            serializer = CarritoSerializer(carrito)
            return Response(serializer.data)

        except ItemCarrito.DoesNotExist:
            return Response(
                {"error": "Item no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def eliminar_item(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "No se puede modificar un carrito completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        item_id = request.data.get('item_id')
        ItemCarrito.objects.filter(id=item_id, carrito=carrito).delete()

        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def iniciar_pago(self, request, pk=None):
        carrito = self.get_object()
        
        if not carrito.items.exists():
            return Response(
                {"error": "El carrito está vacío"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar stock antes de iniciar el pago
        for item in carrito.items.all():
            if item.cantidad > item.stock.cantidad:
                return Response(
                    {
                        "error": f"Stock insuficiente para {item.stock.producto.nombre}",
                        "disponible": item.stock.cantidad,
                        "solicitado": item.cantidad
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Crear orden de compra
        orden = str(carrito.id)
        sesion = str(carrito.id)
        monto = int(carrito.total)
        
        # URL de retorno
        return_url = request.build_absolute_uri(reverse('productos:webpay_return'))

        print("Iniciando transacción con:")
        print(f"- Monto: {monto}")
        print(f"- Orden: {orden}")
        print(f"- Sesión: {sesion}")
        print(f"- URL retorno: {return_url}")

        # Crear transacción en Transbank
        create_request = {
            "buy_order": orden,
            "session_id": sesion,
            "amount": monto,
            "return_url": return_url
        }

        print("Request de creación:", create_request)

        response = tx.create(
            buy_order=orden,
            session_id=sesion,
            amount=monto,
            return_url=return_url
        )

        print("Respuesta de Transbank:", response)

        # Guardar token
        carrito.orden_compra = orden
        carrito.session_id = sesion
        carrito.token_ws = response['token']
        carrito.save()

        return Response({
            "token": response['token'],
            "url": response['url']
        })

@csrf_exempt
def webpay_return(request):
    print("=== INICIO WEBPAY RETURN ===")
    print("Método:", request.method)
    print("POST data:", request.POST)
    print("GET data:", request.GET)

    if request.method == "GET":
        token = request.GET.get('token_ws', None)
        if not token:
            print("Token no encontrado en la solicitud")
            return render(request, 'productos/pago_error.html', {
                'error': 'Token no encontrado'
            })

        print("Token encontrado:", token)
        print("Redirección inicial de Webpay - Creando formulario de confirmación")
        
        return render(request, 'productos/confirmar_pago.html', {
            'token': token
        })

    elif request.method == "POST":
        token = request.POST.get('token_ws', None)
        
        if not token:
            print("Token no encontrado en el POST")
            return render(request, 'productos/pago_error.html', {
                'error': 'Token de transacción no encontrado'
            })
        
        print("Token encontrado:", token)
        print("Confirmando pago con token:", token)

        try:
            response = tx.commit(token=token)
            print("Respuesta de confirmación completa:", response)
            
            if response['status'] == 'AUTHORIZED':
                print("Estado de la transacción:", response['status'])
                print("Código de respuesta:", response['response_code'])

                try:
                    carrito = CarritoCompra.objects.get(token_ws=token)
                    print("Carrito encontrado:", carrito.id)

                    with transaction.atomic():
                        # Actualizar stock
                        for item in carrito.items.all():
                            stock = item.stock
                            stock.cantidad -= item.cantidad
                            stock.save()

                            # Crear venta
                            Venta.objects.create(
                                sucursal=stock.sucursal,
                                producto=stock.producto,
                                cantidad=item.cantidad,
                                precio_unitario=stock.precio,
                                total=item.subtotal
                            )

                        carrito.completado = True
                        carrito.save()
                        print("Compra procesada exitosamente")

                        return render(request, 'productos/pago_exitoso.html', {
                            'response': response,
                            'carrito': carrito
                        })

                except CarritoCompra.DoesNotExist:
                    print("Error: Carrito no encontrado")
                    return render(request, 'productos/pago_error.html', {
                        'error': 'Carrito no encontrado'
                    })

            else:
                print("Error: Transacción no autorizada")
                return render(request, 'productos/pago_error.html', {
                    'error': 'Transacción no autorizada'
                })

        except Exception as e:
            print("Error al procesar el pago:", str(e))
            return render(request, 'productos/pago_error.html', {
                'error': str(e)
            })

    print("=== FIN WEBPAY RETURN ===")
    return render(request, 'productos/pago_error.html', {
        'error': 'Método no soportado'
    })