#!/usr/bin/env python3
"""
Script simple para actualizar las bases de datos de los servidores gRPC
"""
import psycopg2

def actualizar_sucursal(numero):
    """Actualiza la base de datos de una sucursal"""
    print(f"🔄 Actualizando Sucursal {numero}...")
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database=f'sucursal_{numero}',
            user='postgres',
            password='admin'
        )
        cursor = conn.cursor()
        
        # Verificar si la columna stock existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'productos' AND column_name = 'stock'
        """)
        
        if cursor.fetchone():
            print(f"   ✅ Columna 'stock' ya existe")
        else:
            # Agregar la columna stock
            cursor.execute("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0 NOT NULL")
            conn.commit()
            print(f"   ✅ Columna 'stock' agregada")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🗄️  Actualizando bases de datos gRPC...")
    print("=" * 50)
    
    for i in [1, 2, 3]:
        actualizar_sucursal(i)
        print()
    
    print("✅ Proceso completado!")
    print("💡 Reinicia los servidores gRPC: python iniciar_servidores.py")

if __name__ == "__main__":
    main() 