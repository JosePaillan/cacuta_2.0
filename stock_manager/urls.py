from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from productos.views import ProductoViewSet, SucursalViewSet, CarritoViewSet

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'sucursales', SucursalViewSet)
router.register(r'carritos', CarritoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('productos.urls', namespace='productos')),
] 