# Sistema de Gestión de Stock

Sistema de gestión de stock para múltiples sucursales desarrollado con Django y MongoDB.

## Características

- Gestión de productos y stock por sucursal
- Búsqueda de productos
- Visualización de stock y precios por sucursal
- Conversión de precios a USD
- Notificaciones en tiempo real de stock bajo
- API REST completa
- Interfaz web responsive

## Requisitos

- Python 3.8+
- MongoDB 4.4+
- Pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd stock_manager
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar MongoDB:
- Asegúrate de tener MongoDB instalado y ejecutándose
- La base de datos se creará automáticamente al ejecutar las migraciones

5. Realizar migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Crear superusuario (opcional):
```bash
python manage.py createsuperuser
```

## Ejecución

1. Iniciar el servidor de desarrollo:
```bash
python manage.py runserver
```

2. Acceder a la aplicación:
- Interfaz web: http://localhost:8000
- Admin de Django: http://localhost:8000/admin
- API REST: http://localhost:8000/api

## API Endpoints

- `GET /api/productos/`: Lista todos los productos
- `GET /api/productos/?nombre=<búsqueda>`: Busca productos por nombre
- `GET /api/productos/<id>/stock_sucursal/?sucursal=<nombre>`: Obtiene stock y precio de una sucursal
- `GET /api/productos/<id>/precio_usd/?sucursal=<nombre>`: Obtiene precio en USD
- `POST /api/productos/<id>/realizar_venta/`: Realiza una venta

## WebSocket

La aplicación utiliza WebSocket para notificaciones en tiempo real de stock bajo:
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/stock/');
```

## Estructura del Proyecto

```
stock_manager/
├── manage.py
├── requirements.txt
├── stock_manager/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── routing.py
│   └── wsgi.py
└── productos/
    ├── __init__.py
    ├── models.py
    ├── views.py
    ├── consumers.py
    ├── serializers.py
    └── templates/
        └── productos/
            └── index.html
```

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 