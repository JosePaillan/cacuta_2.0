from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Producto, Sucursal, CarritoCompra, ItemCarrito, Venta, AlertaStock
from .serializers import ProductoSerializer, SucursalSerializer, CarritoSerializer, VentaSerializer
from .grpc.clientes import listar_productos_en_sucursal, crear_producto_en_sucursal
from .utils import get_usd_rate
import json
import grpc
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType
from django.http import QueryDict

# Configurar Transbank

webpay_options = WebpayOptions(
    commerce_code="597055555532",
    api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
    integration_type=IntegrationType.TEST
)
tx = Transaction(options=webpay_options)

    
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    @action(detail=False, methods=['post'])
    def crear_en_sucursales(self, request):
        """Crea un producto en todas las sucursales gRPC configuradas"""
        try:
            nombre = request.data.get('nombre')
            descripcion = request.data.get('descripcion', '')
            categoria = request.data.get('categoria')
            precio_local = request.data.get('precio_matriz')
            stock_local = request.data.get('stock_matriz', 0)

            # Extraer precios y stocks por sucursal (formato QueryDict)
            precios = request.data.get('precios', {})
            stocks = request.data.get('stocks', {})

            # Si viene como QueryDict (formulario HTML), convertir a dict
            if isinstance(request.data, QueryDict):
                precios = {k.replace('precios[', '').replace(']', ''): v for k, v in request.data.items() if k.startswith('precios[')}
                stocks = {k.replace('stocks[', '').replace(']', ''): v for k, v in request.data.items() if k.startswith('stocks[')}

            # Validaciones
            errores_validacion = []
            if not nombre:
                errores_validacion.append('El nombre es obligatorio.')
            if not categoria:
                errores_validacion.append('La categoría es obligatoria.')
            if not precio_local:
                errores_validacion.append('El precio base es obligatorio.')
            try:
                stock_local = int(stock_local)
                if stock_local < 0:
                    errores_validacion.append('El stock debe ser un número entero positivo.')
            except (ValueError, TypeError):
                errores_validacion.append('El stock debe ser un número entero.')
            try:
                precio_local = float(precio_local)
                if precio_local < 0:
                    errores_validacion.append('El precio base debe ser un número positivo.')
            except (ValueError, TypeError):
                errores_validacion.append('El precio base debe ser un número.')

            if errores_validacion:
                return Response({'error': ' '.join(errores_validacion)}, status=status.HTTP_400_BAD_REQUEST)

            # Crear producto local
            producto_local, created = Producto.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': descripcion,
                    'categoria': categoria,
                    'precio_base': precio_local,
                    'stock': stock_local
                }
            )

            if not created:
                return Response({
                    'error': 'El producto ya existe localmente'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Crear en sucursales gRPC
            sucursales_exitosas = []
            errores = []
            detalles_sucursales = []

            sucursales = Sucursal.objects.exclude(host__isnull=True).exclude(host='')
            for sucursal in sucursales:
                try:
                    precio_sucursal = float(precios.get(sucursal.host, precio_local))
                    stock_sucursal = int(stocks.get(sucursal.host, stock_local))
                    producto_grpc = crear_producto_en_sucursal(
                        nombre=nombre,
                        descripcion=descripcion,
                        categoria=categoria,
                        precio_base=precio_sucursal,
                        host=sucursal.host,
                        stock=stock_sucursal
                    )
                    sucursales_exitosas.append(sucursal.nombre)
                    detalles_sucursales.append({
                        'sucursal': sucursal.nombre,
                        'id': getattr(producto_grpc, 'id', None),
                        'stock': getattr(producto_grpc, 'stock', None),
                        'precio': getattr(producto_grpc, 'precio_base', None)
                    })
                except Exception as e:
                    errores.append(f"{sucursal.nombre}: {str(e)}")

            return Response({
                'mensaje': 'Producto creado exitosamente',
                'producto_local_id': producto_local.id,
                'stock_local': producto_local.stock,
                'precio_local': producto_local.precio_base,
                'sucursales_exitosas': sucursales_exitosas,
                'detalles_sucursales': detalles_sucursales,
                'errores': errores
            })

        except Exception as e:
            return Response({
                'error': f'Error al crear producto: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self):
        queryset = Producto.objects.all()
        
        # Filtros
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        
        # Ordenamiento
        orden = self.request.query_params.get('orden', 'nombre')
        if orden in ['nombre', 'precio_base', 'stock', 'fecha_creacion']:
            queryset = queryset.order_by(orden)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def stock_sucursal(self, request, pk=None):
        """Obtiene el stock de un producto en una sucursal específica"""
        try:
            producto = self.get_object()
            sucursal_id = request.query_params.get('sucursal_id')
        
            if not sucursal_id:
                return Response({
                    'error': 'Se requiere sucursal_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            sucursal = Sucursal.objects.get(id=sucursal_id)
            
            if not sucursal.host:
                return Response({
                    'error': 'La sucursal no tiene host configurado'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener stock desde gRPC
            productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
            
            for prod in productos_grpc:
                if prod.nombre == producto.nombre:
                    return Response({
                        'producto': producto.nombre,
                        'sucursal': sucursal.nombre,
                        'stock': getattr(prod, 'stock', 0)
                    })
            
            return Response({
                'error': 'Producto no encontrado en la sucursal'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Sucursal.DoesNotExist:
            return Response({
                'error': 'Sucursal no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def inventario_completo(self, request):
        """Obtiene el inventario completo (local + gRPC)"""
        try:
            # Productos locales
            productos_locales = Producto.objects.all()
            inventario_local = []
            
            for producto in productos_locales:
                inventario_local.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'categoria': producto.categoria,
                    'precio_base': producto.precio_base,
                    'stock': producto.stock,
                    'sucursal': 'Local',
                    'es_local': True
                })
            
            # Productos de gRPC
            inventario_grpc = []
            sucursales = Sucursal.objects.exclude(host__isnull=True).exclude(host='')
            
            for sucursal in sucursales:
                try:
                    productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                    
                    for prod in productos_grpc:
                        inventario_grpc.append({
                            'id': f"{sucursal.id}-{prod.id}",
                            'nombre': prod.nombre,
                            'categoria': prod.categoria,
                            'precio_base': prod.precio_base,
                            'stock': getattr(prod, 'stock', 0),
                            'sucursal': sucursal.nombre,
                            'es_local': False
                    })
                except Exception as e:
                    print(f"Error obteniendo productos de {sucursal.nombre}: {str(e)}")
            
            return Response({
                'local': inventario_local,
                'grpc': inventario_grpc
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def realizar_venta(self, request, pk=None):
        """Realiza una venta de un producto"""
        try:
            producto = self.get_object()
            cantidad = int(request.data.get('cantidad', 1))
            sucursal_id = request.data.get('sucursal_id')
            
            if cantidad <= 0:
                return Response({
                    'error': 'La cantidad debe ser mayor a 0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                if sucursal_id:
                    # Venta de producto gRPC
                    sucursal = Sucursal.objects.get(id=sucursal_id)
                    
                    # Verificar stock en gRPC
                    productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                    
                    for prod in productos_grpc:
                        if prod.nombre == producto.nombre:
                            stock_actual = getattr(prod, 'stock', 0)
                            
                            if stock_actual < cantidad:
                                return Response({
                                    'error': f'Stock insuficiente. Disponible: {stock_actual}'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            
                            # Crear venta
                            venta = Venta.objects.create(
                                producto=producto,
                                cantidad=cantidad,
                                precio_unitario=prod.precio_base,
                                total=cantidad * prod.precio_base,
                                es_local=False,
                                sucursal_nombre=sucursal.nombre
                            )
                            
                            return Response({
                                'mensaje': 'Venta realizada exitosamente',
                                'venta_id': venta.id,
                                'total': venta.total
                            })
                    
                    return Response({
                        'error': 'Producto no encontrado en la sucursal'
                    }, status=status.HTTP_404_NOT_FOUND)
                else:
                    # Venta de producto local
                    if producto.stock < cantidad:
                        return Response({
                            'error': f'Stock insuficiente. Disponible: {producto.stock}'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Actualizar stock
                    producto.stock -= cantidad
                    producto.save()
                    
                    # Crear venta
                    venta = Venta.objects.create(
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio_base,
                        total=cantidad * producto.precio_base,
                        es_local=True
                    )
                    
                    # Verificar stock bajo
                    verificar_stock_bajo(producto, producto.stock)
                    
                    return Response({
                        'mensaje': 'Venta realizada exitosamente',
                        'venta_id': venta.id,
                        'total': venta.total
                    })
                    
        except Sucursal.DoesNotExist:
            return Response({
                'error': 'Sucursal no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def precio_usd(self, request, pk=None):
        """Obtiene el precio en USD de un producto"""
        try:
            producto = self.get_object()
            usd_rate = get_usd_rate()
            precio_usd = float(producto.precio_base) * usd_rate
            
            return Response({
                'producto': producto.nombre,
                'precio_clp': float(producto.precio_base),
                'precio_usd': round(precio_usd, 2),
                'tasa_cambio': usd_rate
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def actualizar_stock(self, request, pk=None):
        """Actualiza el stock de un producto"""
        try:
            producto = self.get_object()
            nuevo_stock = int(request.data.get('stock', 0))
            
            if nuevo_stock < 0:
                return Response({
                    'error': 'El stock no puede ser negativo'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            stock_anterior = producto.stock
            producto.stock = nuevo_stock
            producto.save()
            
            # Verificar si el stock quedó bajo
            verificar_stock_bajo(producto, nuevo_stock)
            
            # Enviar notificación SSE si está habilitado
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "stock_notifications",
                    {
                        "type": "stock_notification",
                        "message": f"Stock actualizado: {producto.nombre} - {stock_anterior} → {nuevo_stock}"
                    }
                )
            except:
                pass  # SSE puede no estar disponible

            return Response({'cantidad': producto.stock})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def todos_los_productos(self, request):
        """Obtiene todos los productos locales y de las sucursales gRPC"""
        productos_locales = []
        productos_sucursales = []

        # Obtener productos locales (solo los que tienen stock > 0)
        productos_db = Producto.objects.filter(stock__gt=0)
        for producto in productos_db:
            productos_locales.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'categoria': producto.categoria,
                'precio_base': producto.precio_base,
                'stock': producto.stock,
                'sucursal': None,
                'nombre_sucursal': 'Local',
                'cantidad': producto.stock,
                'es_remoto': False
            })
        
        print("=== DIAGNÓSTICO gRPC ===")
        
        # Obtener todas las sucursales con host configurado
        sucursales_con_host = Sucursal.objects.exclude(host__isnull=True).exclude(host='')
        print(f"Sucursales con host configurado: {sucursales_con_host.count()}")
        
        for sucursal in sucursales_con_host:
            print(f"\n--- Procesando sucursal: {sucursal.nombre} (host: {sucursal.host}) ---")
            try:
                print(f"Intentando conectar a {sucursal.host}...")
                productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                print(f"✅ Productos obtenidos de {sucursal.nombre}: {len(productos_grpc)} productos")
                
                for prod in productos_grpc:
                    stock_actual = getattr(prod, 'stock', 0)
                    print(f"  - Producto: {prod.nombre} (ID: {prod.id}, Stock: {stock_actual})")
                    productos_sucursales.append({
                        'id': f"{sucursal.id}-{prod.id}",
                        'nombre': prod.nombre,
                        'descripcion': prod.descripcion,
                        'categoria': prod.categoria,
                        'precio_base': prod.precio_base,
                        'stock': stock_actual,
                        'sucursal': sucursal.id,
                        'nombre_sucursal': sucursal.nombre,
                        'cantidad': stock_actual,
                        'es_remoto': True
                    })
            except Exception as e:
                print(f"❌ ERROR con sucursal {sucursal.nombre}: {str(e)}")
                print(f"   Tipo de error: {type(e).__name__}")
                # No mostrar el traceback completo para evitar logs muy largos
                print(f"   Continuando con otras sucursales...")

        print(f"\n=== RESUMEN ===")
        print(f"Productos locales con stock: {len(productos_locales)}")
        print(f"Productos de sucursales (todos): {len(productos_sucursales)}")
        print("=== FIN DIAGNÓSTICO ===\n")

        return Response({
            'locales': productos_locales,
            'sucursales': productos_sucursales
        })


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
            # Si sucursal_id es None, es un producto local
            if sucursal_id is None:
                producto = Producto.objects.get(id=producto_id)
                if producto.stock < cantidad:
                    return Response(
                        {"error": "Stock insuficiente"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Para productos locales, crear item directamente
                item, created = ItemCarrito.objects.get_or_create(
                    carrito=carrito,
                    producto=producto,
                    defaults={
                        'cantidad': cantidad,
                        'precio_unitario': producto.precio_base
                    }
                )

                if not created:
                    item.cantidad += cantidad
                    if item.cantidad > producto.stock:
                        return Response(
                            {"error": "Stock insuficiente"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    item.save()
            else:
                # Es un producto remoto - verificar stock en tiempo real
                sucursal = Sucursal.objects.get(id=sucursal_id)
                
                # Obtener stock actual del servidor gRPC
                try:
                    productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                    
                    # Buscar el producto específico
                    producto_grpc = None
                    for prod in productos_grpc:
                        if str(prod.id) == str(producto_id):
                            producto_grpc = prod
                            break
                    
                    if not producto_grpc:
                        return Response(
                            {"error": "Producto no encontrado en la sucursal"},
                            status=status.HTTP_404_NOT_FOUND
                        )
                    
                    stock_actual = getattr(producto_grpc, 'stock', 0)
                    if stock_actual < cantidad:
                        return Response(
                            {"error": f"Stock insuficiente. Disponible: {stock_actual}, Solicitado: {cantidad}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Agregar al carrito
                    item, created = ItemCarrito.objects.get_or_create(
                        carrito=carrito,
                        producto_id_remoto=producto_id,
                        sucursal_id_remoto=sucursal_id,
                        defaults={
                            'cantidad': cantidad,
                            'precio_unitario': producto_grpc.precio_base,
                            'sucursal_nombre': sucursal.nombre
                        }
                    )

                    if not created:
                        item.cantidad += cantidad
                        if item.cantidad > stock_actual:
                            return Response(
                                {"error": "Stock insuficiente"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        item.save()
                        
                except Exception as e:
                    return Response(
                        {"error": f"Error al verificar stock en sucursal: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            serializer = CarritoSerializer(carrito)
            return Response(serializer.data)

        except Producto.DoesNotExist:
            return Response(
                {"error": "Producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Sucursal.DoesNotExist:
            return Response(
                {"error": "Sucursal no encontrada"},
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
        cantidad = int(request.data.get('cantidad', 1))

        try:
            item = ItemCarrito.objects.get(id=item_id, carrito=carrito)
            
            # Verificar stock disponible
            if item.es_local:
                # Producto local
                if cantidad > item.producto.stock:
                    return Response(
                        {"error": "Stock insuficiente"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Producto remoto - verificar stock en tiempo real
                try:
                    sucursal = Sucursal.objects.get(id=item.sucursal_id_remoto)
                    productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                    
                    # Buscar el producto específico
                    producto_grpc = None
                    for prod in productos_grpc:
                        if str(prod.id) == str(item.producto_id_remoto):
                            producto_grpc = prod
                            break
                    
                    if not producto_grpc:
                        return Response(
                            {"error": "Producto no encontrado en la sucursal"},
                            status=status.HTTP_404_NOT_FOUND
                        )
                    
                    stock_actual = getattr(producto_grpc, 'stock', 0)
                    if cantidad > stock_actual:
                        return Response(
                            {"error": f"Stock insuficiente. Disponible: {stock_actual}, Solicitado: {cantidad}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                except Exception as e:
                    return Response(
                        {"error": f"Error al verificar stock en sucursal: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            if item.es_local:
                # Producto local - verificar stock interno
                if item.cantidad > item.producto.stock:
                    return Response(
                        {
                            "error": f"Stock insuficiente para {item.producto.nombre}",
                            "disponible": item.producto.stock,
                            "solicitado": item.cantidad
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Producto remoto - verificar stock en tiempo real
                try:
                    sucursal = Sucursal.objects.get(id=item.sucursal_id_remoto)
                    productos_grpc = listar_productos_en_sucursal(host=sucursal.host)
                    
                    # Buscar el producto específico
                    producto_grpc = None
                    for prod in productos_grpc:
                        if str(prod.id) == str(item.producto_id_remoto):
                            producto_grpc = prod
                            break
                    
                    if not producto_grpc:
                        return Response(
                            {
                                "error": f"Producto {item.nombre_producto} no encontrado en la sucursal"
                            },
                            status=status.HTTP_404_NOT_FOUND
                        )
                    
                    stock_actual = getattr(producto_grpc, 'stock', 0)
                    if item.cantidad > stock_actual:
                        return Response(
                            {
                                "error": f"Stock insuficiente para {item.nombre_producto}",
                                "disponible": stock_actual,
                                "solicitado": item.cantidad
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                except Exception as e:
                    return Response(
                        {
                            "error": f"Error al verificar stock para {item.nombre_producto}: {str(e)}"
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

        try:
            response = tx.create(
                buy_order=orden,
                session_id=sesion,
                amount=monto,
                return_url=return_url
            )
        except Exception as e:
            print(f"🔥 Error creando transacción Transbank: {str(e)}")
            return Response({"error": str(e)}, status=500)

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
                            if item.es_local:
                                # Producto local - actualizar stock interno
                                producto = item.producto
                                producto.stock -= item.cantidad
                                producto.save()
                                
                                # Verificar si el stock quedó bajo
                                verificar_stock_bajo(producto, producto.stock)
                                
                                # Crear venta (sin sucursal para productos locales)
                                Venta.objects.create(
                                    producto=producto,
                                    cantidad=item.cantidad,
                                    precio_unitario=item.precio_unitario,
                                    total=item.subtotal,
                                    es_local=True
                                )
                            else:
                                # Producto remoto - no actualizamos stock aquí (se hace en gRPC)
                                # Solo creamos el registro de venta
                                Venta.objects.create(
                                    producto=Producto.objects.get(id=1),  # Producto genérico
                                    cantidad=item.cantidad,
                                    precio_unitario=item.precio_unitario,
                                    total=item.subtotal,
                                    es_local=False,
                                    sucursal_nombre=item.sucursal_nombre
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

def verificar_stock_bajo(producto, stock_actual, sucursal_nombre=None):
    """
    Verifica si el stock está bajo y crea una alerta si es necesario
    """
    umbral = 5  # Umbral por defecto
    
    if stock_actual <= umbral:
        # Verificar si ya existe una alerta activa para este producto
        alerta_existente = AlertaStock.objects.filter(
            producto=producto,
            activa=True,
            tipo='bajo',
            sucursal_nombre=sucursal_nombre or ''
        ).first()
        
        if not alerta_existente:
            # Crear nueva alerta con información detallada
            if sucursal_nombre:
                mensaje = f"⚠️ Stock bajo en {sucursal_nombre}: {producto.nombre} (Stock: {stock_actual}, Umbral: {umbral})"
            else:
                mensaje = f"⚠️ Stock bajo en Matriz: {producto.nombre} (Stock: {stock_actual}, Umbral: {umbral})"
            
            AlertaStock.objects.create(
                producto=producto,
                sucursal_nombre=sucursal_nombre,
                tipo='bajo',
                mensaje=mensaje,
                stock_actual=stock_actual,
                umbral=umbral
            )
            return True
    
    return False

def sse_alertas_stock(request):
    """
    Endpoint SSE temporalmente deshabilitado
    """
    return Response({'message': 'SSE temporalmente deshabilitado'}, status=503)

@csrf_exempt
def marcar_alerta_resuelta(request, alerta_id):
    """
    Marca una alerta como resuelta
    """
    if request.method == 'POST':
        try:
            alerta = AlertaStock.objects.get(id=alerta_id)
            alerta.activa = False
            alerta.fecha_resuelta = timezone.now()
            alerta.save()
            return Response({'status': 'success', 'message': 'Alerta marcada como resuelta'})
        except AlertaStock.DoesNotExist:
            return Response({'status': 'error', 'message': 'Alerta no encontrada'}, status=404)
    
    return Response({'status': 'error', 'message': 'Método no permitido'}, status=405)

def obtener_alertas(request):
    """
    Endpoint para obtener alertas activas de forma estática
    """
    try:
        alertas_activas = AlertaStock.objects.filter(activa=True).order_by('-fecha_creacion')
        
        alertas_data = []
        for alerta in alertas_activas:
            alertas_data.append({
                'id': alerta.id,
                'tipo': alerta.tipo,
                'mensaje': alerta.mensaje,
                'producto': alerta.producto.nombre,
                'sucursal': alerta.sucursal_nombre if alerta.sucursal_nombre else 'Local',
                'stock_actual': alerta.stock_actual,
                'umbral': alerta.umbral,
                'fecha_creacion': alerta.fecha_creacion.isoformat()
            })
        
            return Response(alertas_data)
        
    except Exception as e:
            return Response({'error': str(e)}, status=500)
