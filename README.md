# Sistema de Gestión de Stock con Transbank

Este es un sistema de gestión de stock con integración de pagos mediante Transbank WebPay Plus.

## Características

- Gestión de productos y stock por sucursal
- Búsqueda de productos
- Visualización de stock y precios por sucursal
- Conversión de precios a USD
- Notificaciones en tiempo real de stock bajo
- API REST completa
- Interfaz web responsive

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Entorno virtual de Python (venv)
- Windows 10 o superior

## Pasos de Instalación

1. **Clonar el Repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd cacuta_2.0
   ```

2. **Crear y Activar el Entorno Virtual**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la Base de Datos**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Configuración de Transbank (Ambiente de Pruebas)

1. **Credenciales de Prueba**
   - Las credenciales ya están configuradas para el ambiente de integración
   - No se requiere modificar nada para pruebas

2. **Datos para Pruebas de Transbank**
   - **Tarjeta de Crédito VISA**
     - Número: `4051 8856 0044 6623`
     - CVV: `123`
     - Fecha de expiración: `Cualquier fecha futura`
   
   - **Datos de Autenticación**
     - RUT: `11.111.111-1`
     - Clave: `123`

3. **Códigos de Respuesta**
   - Para transacción **APROBADA**: usar cualquier monto
   - Para transacción **RECHAZADA**: usar monto exacto de `1001`

## Ejecutar la Aplicación

1. **Iniciar el Servidor con Daphne**
   ```bash
   daphne -b 0.0.0.0 -p 8000 stock_manager.asgi:application
   ```

2. **Acceder a la Aplicación**
   - Abrir el navegador y visitar: `http://localhost:8000`
   - Panel de administración: `http://localhost:8000/admin`

## Flujo de Uso

1. **Gestión de Productos**
   - Agregar productos desde el panel de administración
   - Gestionar stock desde la interfaz principal
   - Buscar productos por nombre

2. **Proceso de Compra**
   - Agregar productos al carrito
   - Iniciar proceso de pago
   - Completar pago con Transbank
   - Verificar confirmación de la transacción

3. **Notificaciones en Tiempo Real**
   - El sistema incluye WebSockets para notificaciones de stock
   - Las actualizaciones se muestran en tiempo real

## Solución de Problemas

1. **Error de Conexión a Transbank**
   - Verificar conexión a internet
   - Confirmar que se está usando el ambiente de integración

2. **Problemas con WebSockets**
   - Asegurarse de usar Daphne como servidor
   - Verificar que no hay otro proceso usando el puerto 8000

3. **Errores de Base de Datos**
   - Ejecutar `python manage.py migrate` nuevamente
   - Verificar permisos de escritura en el directorio

## Detener la Aplicación

1. **Método Normal**
   - Presionar `Ctrl + C` en la terminal

2. **Forzar Cierre**
   ```bash
   taskkill /F /IM daphne.exe
   ```

## Notas Importantes

- El sistema está configurado para ambiente de pruebas de Transbank
- No usar en producción sin cambiar las credenciales
- Mantener actualizado el sistema y sus dependencias
- Realizar copias de seguridad de la base de datos regularmente

## Soporte

Para soporte técnico o consultas, contactar a:
[INFORMACIÓN_DE_CONTACTO]

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