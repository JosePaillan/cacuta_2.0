#!/usr/bin/env python3
"""
Script para iniciar el sistema completo de gestión de stock
Incluye servidores gRPC, limpieza de cache y verificación del sistema
"""
import subprocess
import time
import os
import sys
import signal
from pathlib import Path

def ejecutar_comando_django(comando, descripcion):
    """Ejecuta un comando de Django y muestra el resultado"""
    print(f"\n🔄 {descripcion}...")
    try:
        resultado = subprocess.run(
            [sys.executable, "manage.py"] + comando.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if resultado.returncode == 0:
            print(f"✅ {descripcion} completado")
            if resultado.stdout.strip():
                print(f"   Output: {resultado.stdout.strip()}")
        else:
            print(f"⚠️  {descripcion} con advertencias")
            if resultado.stderr.strip():
                print(f"   Error: {resultado.stderr.strip()}")
                
    except subprocess.TimeoutExpired:
        print(f"⏰ {descripcion} tardó demasiado")
    except Exception as e:
        print(f"❌ Error en {descripcion}: {e}")

def limpiar_sistema():
    """Limpia el sistema antes de iniciar"""
    print("🧹 Limpiando sistema...")
    
    # Limpiar cache SSE
    ejecutar_comando_django("limpiar_sse --limpiar-cache", "Limpiando cache SSE")
    
    # Verificar servidores
    ejecutar_comando_django("verificar_servidores", "Verificando estado de servidores")

def iniciar_servidores_grpc():
    """Inicia los servidores gRPC"""
    print("\n🚀 Iniciando servidores gRPC...")
    
    sucursales = [
        (1, 50052),
        (2, 50053), 
        (3, 50054)
    ]
    
    procesos = []
    
    for numero_sucursal, puerto in sucursales:
        sucursal_dir = Path(f"Api_Flask/Sucursal_{numero_sucursal}")
        
        if not sucursal_dir.exists():
            print(f"❌ No se encontró {sucursal_dir}")
            continue
        
        try:
            print(f"   🔄 Iniciando Sucursal {numero_sucursal} (puerto {puerto})...")
            
            # Cambiar al directorio de la sucursal
            os.chdir(sucursal_dir)
            
            proceso = subprocess.Popen(
                [sys.executable, "server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Volver al directorio raíz
            os.chdir(Path(__file__).parent)
            
            # Esperar un momento para verificar que se inició
            time.sleep(2)
            
            if proceso.poll() is None:
                print(f"   ✅ Sucursal {numero_sucursal} iniciada (PID: {proceso.pid})")
                procesos.append((numero_sucursal, proceso))
            else:
                stdout, stderr = proceso.communicate()
                print(f"   ❌ Error al iniciar Sucursal {numero_sucursal}")
                if stderr.strip():
                    print(f"      Error: {stderr.strip()}")
                    
        except Exception as e:
            print(f"   ❌ Error al iniciar Sucursal {numero_sucursal}: {e}")
    
    return procesos

def verificar_sistema():
    """Verifica que todo el sistema esté funcionando"""
    print("\n🔍 Verificando sistema completo...")
    
    # Verificar servidores gRPC
    ejecutar_comando_django("verificar_servidores", "Verificando servidores gRPC")
    
    # Crear datos de prueba si no existen
    ejecutar_comando_django("test_sistema_completo --crear-productos", "Creando productos de prueba")
    
    # Crear alertas de prueba
    ejecutar_comando_django("test_sistema_completo --crear-alertas", "Creando alertas de prueba")

def mostrar_instrucciones():
    """Muestra las instrucciones para usar el sistema"""
    print("\n" + "=" * 60)
    print("🎉 SISTEMA INICIADO CORRECTAMENTE!")
    print("=" * 60)
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. En otra terminal, ejecuta:")
    print("   python manage.py runserver")
    print("\n2. Abre tu navegador en:")
    print("   http://localhost:8000")
    print("\n3. Para verificar el estado:")
    print("   python manage.py verificar_servidores")
    print("\n4. Para limpiar el sistema:")
    print("   python manage.py limpiar_sse --todo")
    print("\n🛑 Para detener los servidores gRPC:")
    print("   Presiona Ctrl+C en esta terminal")
    print("\n" + "=" * 60)

def main():
    """Función principal"""
    print("🚀 INICIANDO SISTEMA COMPLETO DE GESTIÓN DE STOCK")
    print("=" * 60)
    
    # Limpiar sistema
    limpiar_sistema()
    
    # Iniciar servidores gRPC
    procesos = iniciar_servidores_grpc()
    
    if not procesos:
        print("\n❌ No se pudieron iniciar los servidores gRPC")
        print("💡 Verifica que los directorios Api_Flask/Sucursal_X existan")
        return
    
    # Esperar un momento para que los servidores se estabilicen
    print("\n⏳ Esperando que los servidores se estabilicen...")
    time.sleep(5)
    
    # Verificar sistema
    verificar_sistema()
    
    # Mostrar instrucciones
    mostrar_instrucciones()
    
    # Mantener el script ejecutándose
    try:
        print("\n🔄 Manteniendo servidores ejecutándose...")
        print("💡 Los servidores gRPC están activos")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servidores...")
        
        for numero_sucursal, proceso in procesos:
            try:
                proceso.terminate()
                proceso.wait(timeout=5)
                print(f"✅ Servidor Sucursal {numero_sucursal} detenido")
            except subprocess.TimeoutExpired:
                proceso.kill()
                print(f"⚠️  Servidor Sucursal {numero_sucursal} forzado a detener")
        
        print("\n👋 Todos los servidores detenidos")
        print("💡 Sistema cerrado correctamente")

if __name__ == "__main__":
    main() 