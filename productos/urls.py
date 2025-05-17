from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views

app_name = 'productos'

router = DefaultRouter()
router.register(r'productos', views.ProductoViewSet)
router.register(r'sucursales', views.SucursalViewSet)
router.register(r'carritos', views.CarritoViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('', TemplateView.as_view(template_name='productos/index.html'), name='lista_productos'),
    path('carrito/', TemplateView.as_view(template_name='productos/carrito.html'), name='carrito'),
    path('webpay/return/', views.webpay_return, name='webpay_return'),
] 