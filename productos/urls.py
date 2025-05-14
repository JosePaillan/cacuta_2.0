from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'productos', views.ProductoViewSet)
router.register(r'sucursales', views.SucursalViewSet)
router.register(r'carritos', views.CarritoViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('webpay/return/', views.webpay_return, name='webpay_return'),
] 