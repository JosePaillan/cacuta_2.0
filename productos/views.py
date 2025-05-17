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

from .models import Producto, Sucursal, ProductoSucursal, CarritoCompra, ItemCarrito, Venta
from .serializers import ProductoSerializer, VentaSerializer, SucursalSerializer, ProductoSucursalSerializer, CarritoSerializer, ItemCarritoSerializer

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
            producto_sucursal = ProductoSucursal.objects.get(
                producto=producto,
                sucursal_id=sucursal_id
            )
            serializer = ProductoSucursalSerializer(producto_sucursal)
            return Response(serializer.data)
        except ProductoSucursal.DoesNotExist:
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
                producto_sucursal = ProductoSucursal.objects.get(
                    producto=producto,
                    sucursal_id=serializer.validated_data['sucursal_id']
                )

                cantidad = serializer.validated_data['cantidad']

                # Verificar stock
                if producto_sucursal.stock < cantidad:
                    return Response(
                        {"error": "Stock insuficiente"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Crear la venta
                venta = Venta.objects.create(
                    sucursal=producto_sucursal.sucursal,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto_sucursal.precio,
                    total=producto_sucursal.precio * cantidad
                )

                # Actualizar stock
                producto_sucursal.stock -= cantidad
                producto_sucursal.save()

                # Notificar si el stock es bajo
                if producto_sucursal.stock <= 5:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "stock_notifications",
                        {
                            "type": "stock_notification",
                            "message": f"¡Alerta! Stock bajo ({producto_sucursal.stock} unidades) en {producto_sucursal.sucursal.nombre} para {producto.nombre}"
                        }
                    )

                return Response({
                    "mensaje": "Venta realizada con éxito",
                    "venta_id": venta.id,
                    "nuevo_stock": producto_sucursal.stock
                })
        except ProductoSucursal.DoesNotExist:
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
                producto_sucursal = ProductoSucursal.objects.get(
                    producto=producto,
                    sucursal_id=sucursal_id
                )
                precio_usd = Decimal(str(producto_sucursal.precio)) / tipo_cambio
                return Response({
                    "precio_usd": round(precio_usd, 2)
                })
            except ProductoSucursal.DoesNotExist:
                return Response(
                    {"error": "Sucursal no encontrada para este producto"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            precio_usd = Decimal(str(producto.precio_casa_matriz)) / tipo_cambio
            return Response({
                "precio_usd": round(precio_usd, 2)
            })

    @action(detail=True, methods=['post'])
    def actualizar_stock(self, request, pk=None):
        try:
            producto = self.get_object()
            sucursal_id = request.data.get('sucursal_id')
            nuevo_stock = request.data.get('stock')
            
            if nuevo_stock is None:
                return Response({'error': 'Debe proporcionar el nuevo stock'}, status=400)
            
            if sucursal_id is None:
                return Response({'error': 'Debe proporcionar el ID de la sucursal'}, status=400)
            
            try:
                producto_sucursal = ProductoSucursal.objects.get(
                    producto=producto,
                    sucursal_id=sucursal_id
                )
            except ProductoSucursal.DoesNotExist:
                return Response({'error': 'No se encontró el producto en la sucursal especificada'}, status=404)
            
            producto_sucursal.stock = nuevo_stock
            producto_sucursal.save()

            # Notificar si el stock es bajo (menor o igual a 5)
            if producto_sucursal.stock <= 5:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "stock_notifications",
                    {
                        "type": "stock_notification",
                        "message": f"¡Alerta! Stock bajo ({producto_sucursal.stock} unidades) en {producto_sucursal.sucursal.nombre} para {producto_sucursal.producto.nombre}"
                    }
                )

            return Response({'stock': producto_sucursal.stock})
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
            usuario='anonymous',
            completado=False
        ).first()

        if not carrito:
            carrito = CarritoCompra.objects.create(usuario='anonymous')

        serializer = self.get_serializer(carrito)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def agregar_item(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "Este carrito ya está completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ItemCarritoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    producto_sucursal = serializer.validated_data['producto_sucursal']
                    cantidad = serializer.validated_data['cantidad']

                    # Verificar stock disponible
                    if producto_sucursal.stock < cantidad:
                        return Response(
                            {"error": "Stock insuficiente"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    try:
                        item = ItemCarrito.objects.get(
                            carrito=carrito,
                            producto_sucursal=producto_sucursal
                        )
                        item.cantidad += cantidad
                        item.full_clean()
                        item.save()
                    except ItemCarrito.DoesNotExist:
                        serializer.save(carrito=carrito)

                    return Response(CarritoSerializer(carrito).data)
            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def actualizar_item(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "Este carrito ya está completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                item = carrito.items.get(id=request.data.get('item_id'))
                nueva_cantidad = request.data.get('cantidad', item.cantidad)

                # Verificar stock disponible
                if item.producto_sucursal.stock < nueva_cantidad:
                    return Response(
                        {"error": "Stock insuficiente"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                item.cantidad = nueva_cantidad
                item.full_clean()
                item.save()
                return Response(CarritoSerializer(carrito).data)
        except (ItemCarrito.DoesNotExist, ValidationError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def eliminar_item(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "Este carrito ya está completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = carrito.items.get(id=request.data.get('item_id'))
            item.delete()
            return Response(CarritoSerializer(carrito).data)
        except ItemCarrito.DoesNotExist:
            return Response(
                {"error": "Item no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "Este carrito ya está completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                for item in carrito.items.all():
                    producto_sucursal = item.producto_sucursal
                    if producto_sucursal.stock < item.cantidad:
                        raise ValidationError(
                            f"Stock insuficiente para {item.producto_sucursal.producto.nombre}"
                        )
                    
                    # Crear venta y actualizar stock
                    Venta.objects.create(
                        sucursal=producto_sucursal.sucursal,
                        producto=producto_sucursal.producto,
                        cantidad=item.cantidad,
                        precio_unitario=producto_sucursal.precio,
                        total=item.subtotal
                    )
                    producto_sucursal.stock -= item.cantidad
                    producto_sucursal.save()

                    # Notificar si el stock es bajo
                    if producto_sucursal.stock <= 5:
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            "stock_notifications",
                            {
                                "type": "stock_notification",
                                "message": f"¡Alerta! Stock bajo ({producto_sucursal.stock} unidades) en {producto_sucursal.sucursal.nombre} para {producto_sucursal.producto.nombre}"
                            }
                        )
                
                carrito.completado = True
                carrito.save()
                return Response({"mensaje": "Compra completada con éxito"})
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post', 'get'])
    def confirmar_pago(self, request, pk=None):
        carrito = self.get_object()
        
        # Si es GET, mostrar página de espera
        if request.method == 'GET':
            return render(request, 'productos/webpay_return.html')
        
        # Obtener el token del POST o GET
        token = request.POST.get('token_ws') or request.GET.get('token_ws')
        
        if not token:
            return render(request, 'productos/webpay_return.html', {
                'error': 'Token no proporcionado'
            })
        
        try:
            print(f"Confirmando pago con token: {token}")  # Debug log
            response = tx.commit(token=token)
            print(f"Respuesta de confirmación: {response.__dict__ if hasattr(response, '__dict__') else response}")
            
            if hasattr(response, 'status'):
                status = response.status
            elif isinstance(response, dict):
                status = response.get('status')
            else:
                status = str(response)
            
            print(f"Estado de la transacción: {status}")
            
            if status == 'AUTHORIZED':
                with transaction.atomic():
                    # Procesar la compra
                    for item in carrito.items.all():
                        producto_sucursal = item.producto_sucursal
                        if producto_sucursal.stock < item.cantidad:
                            raise ValidationError(
                                f"Stock insuficiente para {item.producto_sucursal.producto.nombre}"
                            )
                        
                        Venta.objects.create(
                            sucursal=producto_sucursal.sucursal,
                            producto=producto_sucursal.producto,
                            cantidad=item.cantidad,
                            precio_unitario=producto_sucursal.precio,
                            total=item.subtotal
                        )
                        producto_sucursal.stock -= item.cantidad
                        producto_sucursal.save()

                        if producto_sucursal.stock <= 5:
                            channel_layer = get_channel_layer()
                            async_to_sync(channel_layer.group_send)(
                                "stock_notifications",
                                {
                                    "type": "stock_notification",
                                    "message": f"¡Alerta! Stock bajo ({producto_sucursal.stock} unidades) en {producto_sucursal.sucursal.nombre} para {producto_sucursal.producto.nombre}"
                                }
                            )
                    
                    carrito.completado = True
                    carrito.save()
                
                return render(request, 'productos/webpay_return.html', {
                    'success': True,
                    'response': {
                        'authorization_code': getattr(response, 'authorization_code', ''),
                        'amount': getattr(response, 'amount', ''),
                        'buy_order': getattr(response, 'buy_order', ''),
                        'response_code': getattr(response, 'response_code', '')
                    }
                })
            else:
                print(f"Pago rechazado con estado: {status}")
                return render(request, 'productos/webpay_return.html', {
                    'error': 'Pago rechazado',
                    'status': status
                })
                
        except Exception as e:
            print(f"Error en confirmación: {str(e)}")
            print(f"Tipo de error: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return render(request, 'productos/webpay_return.html', {
                'error': str(e)
            })

    @action(detail=True, methods=['post'])
    def iniciar_pago(self, request, pk=None):
        carrito = self.get_object()
        if carrito.completado:
            return Response(
                {"error": "Este carrito ya está completado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Calcular el monto total
            monto_total = int(sum(item.subtotal for item in carrito.items.all()))
            if monto_total <= 0:
                return Response(
                    {"error": "El carrito está vacío"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear la transacción en Transbank
            buy_order = str(carrito.id)
            session_id = str(carrito.id)
            
            # URL de retorno
            return_url = "http://127.0.0.1:8000/webpay/return/"
            
            print("Iniciando transacción con:")
            print(f"- Monto: {monto_total}")
            print(f"- Orden: {buy_order}")
            print(f"- Sesión: {session_id}")
            print(f"- URL retorno: {return_url}")
            
            # Crear la transacción
            create_request = {
                "buy_order": buy_order,
                "session_id": session_id,
                "amount": monto_total,
                "return_url": return_url
            }
            print("Request de creación:", create_request)
            
            response = tx.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=monto_total,
                return_url=return_url
            )
            
            print("Respuesta de Transbank:", response)
            
            # Guardar los datos de la transacción en el carrito
            carrito.orden_compra = buy_order
            carrito.session_id = session_id
            carrito.token_ws = response.token if hasattr(response, 'token') else response['token']
            carrito.save()
            
            # Retornar la URL y el token
            return Response({
                "url": response.url if hasattr(response, 'url') else response['url'],
                "token": response.token if hasattr(response, 'token') else response['token']
            })
            
        except Exception as e:
            print(f"Error al iniciar pago: {str(e)}")
            print(f"Tipo de error: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@csrf_exempt
def webpay_return(request):
    print("=== INICIO WEBPAY RETURN ===")
    print("Método:", request.method)
    print("POST data:", request.POST)
    print("GET data:", request.GET)
    
    # Obtener el token de POST o GET
    token = request.POST.get('token_ws') or request.GET.get('token_ws')
    
    if not token:
        print("Token no encontrado en la solicitud")
        return render(request, 'productos/webpay_return.html', {
            'error': 'Token no proporcionado'
        })
    
    print(f"Token encontrado: {token}")
    
    try:
        # Si es GET, significa que Webpay está haciendo la redirección inicial
        if request.method == 'GET':
            print("Redirección inicial de Webpay - Creando formulario de confirmación")
            # Crear un formulario para hacer el POST de confirmación
            return render(request, 'productos/webpay_confirm.html', {
                'token': token,
                'return_url': request.path
            })
        
        print(f"Confirmando pago con token: {token}")
        response = tx.commit(token=token)
        print(f"Respuesta de confirmación completa: {response.__dict__ if hasattr(response, '__dict__') else response}")
        
        # Extraer el estado de la transacción
        if hasattr(response, 'status'):
            status = response.status
        elif isinstance(response, dict):
            status = response.get('status')
        else:
            status = str(response)
        
        print(f"Estado de la transacción: {status}")
        
        # Extraer el código de respuesta si existe
        response_code = None
        if hasattr(response, 'response_code'):
            response_code = response.response_code
        elif isinstance(response, dict):
            response_code = response.get('response_code')
        
        print(f"Código de respuesta: {response_code}")
        
        if status == 'AUTHORIZED':
            try:
                carrito = CarritoCompra.objects.get(token_ws=token)
                print(f"Carrito encontrado: {carrito.id}")
                
                with transaction.atomic():
                    # Procesar la compra
                    for item in carrito.items.all():
                        producto_sucursal = item.producto_sucursal
                        if producto_sucursal.stock < item.cantidad:
                            raise ValidationError(
                                f"Stock insuficiente para {item.producto_sucursal.producto.nombre}"
                            )
                        
                        Venta.objects.create(
                            sucursal=producto_sucursal.sucursal,
                            producto=producto_sucursal.producto,
                            cantidad=item.cantidad,
                            precio_unitario=producto_sucursal.precio,
                            total=item.subtotal
                        )
                        producto_sucursal.stock -= item.cantidad
                        producto_sucursal.save()

                        if producto_sucursal.stock <= 5:
                            channel_layer = get_channel_layer()
                            async_to_sync(channel_layer.group_send)(
                                "stock_notifications",
                                {
                                    "type": "stock_notification",
                                    "message": f"¡Alerta! Stock bajo ({producto_sucursal.stock} unidades) en {producto_sucursal.sucursal.nombre} para {producto_sucursal.producto.nombre}"
                                }
                            )
                    
                    carrito.completado = True
                    carrito.save()
                    print("Compra procesada exitosamente")
                
                return render(request, 'productos/webpay_return.html', {
                    'success': True,
                    'response': {
                        'authorization_code': getattr(response, 'authorization_code', ''),
                        'amount': getattr(response, 'amount', ''),
                        'buy_order': getattr(response, 'buy_order', ''),
                        'response_code': response_code
                    }
                })
            except CarritoCompra.DoesNotExist:
                error_msg = f"No se encontró el carrito con token: {token}"
                print(error_msg)
                return render(request, 'productos/webpay_return.html', {
                    'error': error_msg,
                    'status': status
                })
            except ValidationError as e:
                error_msg = f"Error de validación: {str(e)}"
                print(error_msg)
                return render(request, 'productos/webpay_return.html', {
                    'error': error_msg,
                    'status': status
                })
        else:
            error_msg = f"Pago rechazado con estado: {status}"
            if response_code:
                error_msg += f" (código: {response_code})"
            print(error_msg)
            return render(request, 'productos/webpay_return.html', {
                'error': error_msg,
                'status': status
            })
            
    except Exception as e:
        print(f"Error en confirmación: {str(e)}")
        print(f"Tipo de error: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render(request, 'productos/webpay_return.html', {
            'error': f"Error procesando el pago: {str(e)}"
        })
    finally:
        print("=== FIN WEBPAY RETURN ===")