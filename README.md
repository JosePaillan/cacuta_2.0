## Primero hay que instalar postgre y definir tu contraseña esta debe guardarla
## Crear las base de datos
En postgre debes crear cuatro base de datos

   CREATE DATABASE sucursal_2;
   CREATE DATABASE sucursal_3;
   CREATE DATABASE cacuta_db;
   CREATE DATABASE sucursal_1;

Para las conexiones se considero como usuario 'postgre' y contraseña 'admin'

Debes crear un entorno virtual con el comando

python -m venv .env

Debes activar el entorno virtual e instalara todas las dependecias con

pip install -r requirements.txt

Para iniciar el proyecto primero debes crear las migraciones y luego ejecturalas

python manage.py makemigrations
python manage.py migrate

Para lanza el servidor debes utilizar el comando

daphne -b 0.0.0.0 -p 8000 stock_manager.asgi:application

Para lanzar los servidores flask debes utilizar el comando 

python iniciar_servidores.py