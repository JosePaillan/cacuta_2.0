from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from productos.views import ProductoViewSet, SucursalViewSet, CarritoViewSet
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'sucursales', SucursalViewSet)
router.register(r'carritos', CarritoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('', TemplateView.as_view(template_name='productos/index.html'), name='home'),
    path('carrito/', TemplateView.as_view(template_name='productos/carrito.html'), name='carrito'),
    path('', include('productos.urls')),
] 