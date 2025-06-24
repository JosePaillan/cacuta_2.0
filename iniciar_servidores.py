#!/usr/bin/env python3
"""
Script para iniciar automáticamente todos los servidores gRPC
"""
import subprocess
import time
import os
import sys
from pathlib import Path

def iniciar_servidor_sucursal(numero_sucursal, puerto):
    """Inicia un servidor gRPC para una sucursal específica"""
    sucursal_dir = Path(f"Api_Flask/Sucursal_{numero_sucursal}")
    
    if not sucursal_dir.exists():
        print(f"❌ Error: No se encontró el directorio {sucursal_dir}")
        return None
    
    # Cambiar al directorio de la sucursal
    os.chdir(sucursal_dir)
    
    # Comando para iniciar el servidor
    comando = [sys.executable, "server.py"]
    
    try:
        print(f"🚀 Iniciando servidor Sucursal {numero_sucursal} en puerto {puerto}...")
        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Esperar un momento para verificar que el servidor se inició correctamente
        time.sleep(2)
        
        if proceso.poll() is None:
            print(f"✅ Servidor Sucursal {numero_sucursal} iniciado correctamente (PID: {proceso.pid})")
            return proceso
        else:
            stdout, stderr = proceso.communicate()
            print(f"❌ Error al iniciar servidor Sucursal {numero_sucursal}:")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error al iniciar servidor Sucursal {numero_sucursal}: {e}")
        return None
    finally:
        # Volver al directorio raíz
        os.chdir(Path(__file__).parent)

def main():
    """Función principal"""
    print("🔄 Iniciando servidores gRPC...")
    print("=" * 50)
    
    # Configuración de sucursales
    sucursales = [
        (1, 50052),
        (2, 50053), 
        (3, 50054)
    ]
    
    procesos = []
    
    # Iniciar cada servidor
    for numero_sucursal, puerto in sucursales:
        proceso = iniciar_servidor_sucursal(numero_sucursal, puerto)
        if proceso:
            procesos.append((numero_sucursal, proceso))
        time.sleep(1)  # Pequeña pausa entre servidores
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN:")
    print(f"✅ Servidores iniciados: {len(procesos)}/{len(sucursales)}")
    
    for numero_sucursal, proceso in procesos:
        print(f"   - Sucursal {numero_sucursal}: PID {proceso.pid}")
    
    if len(procesos) == len(sucursales):
        print("\n🎉 Todos los servidores iniciados correctamente!")
        print("💡 Ahora puedes ejecutar el servidor Django:")
        print("   python manage.py runserver")
    else:
        print(f"\n⚠️  Solo {len(procesos)} de {len(sucursales)} servidores se iniciaron")
        print("   Revisa los errores anteriores")
    
    print("\n🛑 Para detener todos los servidores, presiona Ctrl+C")
    
    try:
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidores...")
        for numero_sucursal, proceso in procesos:
            try:
                proceso.terminate()
                proceso.wait(timeout=5)
                print(f"✅ Servidor Sucursal {numero_sucursal} detenido")
            except subprocess.TimeoutExpired:
                proceso.kill()
                print(f"⚠️  Servidor Sucursal {numero_sucursal} forzado a detener")
        print("👋 Todos los servidores detenidos")

if __name__ == "__main__":
    main() 