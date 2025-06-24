#!/usr/bin/env python3
"""
Script para actualizar las bases de datos de los servidores gRPC
Agrega la columna 'stock' a las tablas de productos existentes
"""
import psycopg2
import sys
from pathlib import Path

def actualizar_base_datos_sucursal(numero_sucursal, puerto):
    """Actualiza la base de datos de una sucursal específica"""
    print(f"🔄 Actualizando base de datos Sucursal {numero_sucursal}...")
    
    # Configuración de la base de datos
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': f'sucursal_{numero_sucursal}',
        'user': 'postgres',
        'password': 'admin'
    }
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Verificar si la columna stock ya existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'productos' AND column_name = 'stock'
        """)
        
        if cursor.fetchone():
            print(f"   ✅ Columna 'stock' ya existe en Sucursal {numero_sucursal}")
        else:
            # Agregar la columna stock
            cursor.execute("""
                ALTER TABLE productos 
                ADD COLUMN stock INTEGER DEFAULT 0 NOT NULL
            """)
            
            # Agregar constraint para stock no negativo
            cursor.execute("""
                ALTER TABLE productos 
                ADD CONSTRAINT check_stock_non_negative CHECK (stock >= 0)
            """)
            
            conn.commit()
            print(f"   ✅ Columna 'stock' agregada a Sucursal {numero_sucursal}")
        
        # Verificar la estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'productos'
            ORDER BY ordinal_position
        """)
        
        columnas = cursor.fetchall()
        print(f"   📋 Estructura de tabla productos en Sucursal {numero_sucursal}:")
        for col in columnas:
            print(f"      • {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"   ❌ Error en Sucursal {numero_sucursal}: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado en Sucursal {numero_sucursal}: {e}")
        return False

def main():
    """Función principal"""
    print("🗄️  ACTUALIZANDO BASES DE DATOS DE SERVIDORES gRPC")
    print("=" * 60)
    
    # Configuración de sucursales
    sucursales = [
        (1, 50052),
        (2, 50053), 
        (3, 50054)
    ]
    
    exitos = 0
    errores = 0
    
    for numero_sucursal, puerto in sucursales:
        if actualizar_base_datos_sucursal(numero_sucursal, puerto):
            exitos += 1
        else:
            errores += 1
        print()  # Línea en blanco
    
    # Resumen
    print("=" * 60)
    print("📊 RESUMEN:")
    print(f"   ✅ Bases de datos actualizadas: {exitos}")
    print(f"   ❌ Errores: {errores}")
    
    if errores == 0:
        print("\n🎉 Todas las bases de datos actualizadas correctamente!")
        print("💡 Ahora puedes crear productos sin problemas")
    else:
        print(f"\n⚠️  {errores} base(s) de datos tuvieron problemas")
        print("💡 Verifica la configuración de PostgreSQL")
    
    print("\n🔄 Para aplicar los cambios, reinicia los servidores gRPC:")
    print("   python iniciar_servidores.py")

if __name__ == "__main__":
    main() 