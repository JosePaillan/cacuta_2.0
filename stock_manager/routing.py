from django.urls import re_path
from productos.consumers import StockConsumer

websocket_urlpatterns = [
    re_path(r'ws/stock/$', StockConsumer.as_asgi()),
] 