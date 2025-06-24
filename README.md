# Sistema de Gestión de Stock Distribuido (Django + Flask/gRPC)

## 1. Requisitos

- **Python 3.10+**
- **PostgreSQL** (instalado y corriendo)
- **pip** (gestor de paquetes de Python)
- **git** (opcional, para clonar el repo)

## 2. Instalación de dependencias

### a) Crear y activar entorno virtual

```bash
python -m venv .env
# En Windows:
.env\Scripts\activate
# En Linux/Mac:
source .env/bin/activate
```

### b) Instalar dependencias principales

```bash
pip install -r requirements.txt
```

**Contenido de `requirements.txt`:**
```
asgiref==3.8.1
attrs==25.3.0
autobahn==24.4.2
Automat==25.4.16
blinker==1.9.0
certifi==2025.6.15
cffi==1.17.1
channels==4.0.0
charset-normalizer==3.4.2
click==8.2.1
colorama==0.4.6
constantly==23.10.4
cryptography==45.0.4
daphne==4.2.0
Django==4.2
django-cors-headers==4.3.1
djangorestframework==3.14.0
Flask==3.1.1
greenlet==3.2.3
grpcio==1.73.0
grpcio-tools==1.73.0
hyperlink==21.0.0
idna==3.10
incremental==24.7.2
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
marshmallow==3.26.1
packaging==25.0
protobuf==6.31.1
psycopg2-binary==2.9.10
pyasn1==0.6.1
pyasn1_modules==0.4.2
pycparser==2.22
pyOpenSSL==25.1.0
python-dotenv==1.0.1
pytz==2025.2
requests==2.31.0
service-identity==24.2.0
setuptools==80.9.0
SQLAlchemy==2.0.41
sqlparse==0.5.3
transbank-sdk==6.0.0
Twisted==25.5.0
txaio==23.1.1
typing_extensions==4.14.0
tzdata==2025.2
urllib3==2.5.0
Werkzeug==3.1.3
zope.interface==7.2
```

### c) Dependencias para servidores Flask/gRPC de sucursales

Cada sucursal tiene su propio `requirements.txt` (idéntico):

```
grpcio
grpcio-tools
Flask
SQLAlchemy
psycopg2-binary
```

## 3. Configuración de la base de datos

### a) Crear las bases de datos en PostgreSQL

Conéctate a PostgreSQL y ejecuta:

```sql
CREATE DATABASE cacuta_db;
CREATE DATABASE sucursal_1;
CREATE DATABASE sucursal_2;
CREATE DATABASE sucursal_3;
```

- Usuario recomendado: `postgres`
- Contraseña recomendada: `admin`
- Puedes cambiar estos valores en los settings y en el app de cada sucursal si lo necesitas.

### b) Configura el usuario y contraseña en tu PostgreSQL si es necesario.

## 4. Migraciones Django

```bash
python manage.py makemigrations
python manage.py migrate
```

## 5. Compilar los archivos gRPC (si modificas productos.proto)

Si cambias el archivo `productos.proto`, debes regenerar los archivos Python para gRPC:

```bash
python -m grpc_tools.protoc -I. --python_out=productos/grpc --grpc_python_out=productos/grpc productos.proto
```

Haz esto cada vez que cambies el archivo `.proto`.

## 6. Iniciar los servidores gRPC de las sucursales

Puedes iniciar todos los servidores de las sucursales automáticamente con:

```bash
python iniciar_servidores.py
```

Esto lanzará:
- Sucursal 1 en `localhost:50052`
- Sucursal 2 en `localhost:50053`
- Sucursal 3 en `localhost:50054`



## 7. Configurar los hosts de las sucursales en Django

Ejecuta el script para registrar los hosts de las sucursales en la base de datos Django:

```bash
python configurar_hosts.py
```

Esto asociará los nombres de sucursal con sus puertos gRPC.

## 8. Iniciar el servidor principal Django/ASGI

```bash
daphne -b 0.0.0.0 -p 8000 stock_manager.asgi:application
```

---

**Notas:**
- Si tienes problemas de conexión gRPC, asegúrate de que los puertos no estén ocupados y que los servidores estén corriendo.
- Si cambias la estructura de la base de datos de las sucursales, revisa los scripts de migración y el archivo `productos.proto`.
- Para detener los servidores de las sucursales, presiona `Ctrl+C` en la terminal donde ejecutaste `iniciar_servidores.py`.

---

¿Quieres que agregue alguna sección extra (por ejemplo, troubleshooting, comandos útiles, o explicación de la arquitectura)?