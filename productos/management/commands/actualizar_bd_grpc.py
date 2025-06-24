from django.core.management.base import BaseCommand
import psycopg2

class Command(BaseCommand):
    help = 'Actualiza las bases de datos de los servidores gRPC agregando la columna stock'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🗄️  Actualizando bases de datos gRPC...')
        )
        self.stdout.write('=' * 50)
        
        exitos = 0
        errores = 0
        
        for numero in [1, 2, 3]:
            self.stdout.write(f'\n🔄 Actualizando Sucursal {numero}...')
            
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
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Columna "stock" ya existe en Sucursal {numero}')
                    )
                else:
                    # Agregar la columna stock
                    cursor.execute("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0 NOT NULL")
                    conn.commit()
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Columna "stock" agregada a Sucursal {numero}')
                    )
                
                cursor.close()
                conn.close()
                exitos += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error en Sucursal {numero}: {e}')
                )
                errores += 1
        
        # Resumen
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('📊 RESUMEN:')
        self.stdout.write(f'   ✅ Bases de datos actualizadas: {exitos}')
        self.stdout.write(f'   ❌ Errores: {errores}')
        
        if errores == 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Todas las bases de datos actualizadas correctamente!')
            )
            self.stdout.write('💡 Ahora puedes crear productos sin problemas')
        else:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  {errores} base(s) de datos tuvieron problemas')
            )
            self.stdout.write('💡 Verifica la configuración de PostgreSQL')
        
        self.stdout.write('\n🔄 Para aplicar los cambios, reinicia los servidores gRPC:')
        self.stdout.write('   python iniciar_servidores.py') 