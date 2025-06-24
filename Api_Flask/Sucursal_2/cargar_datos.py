from app import SessionLocal
from models import Producto

productos = [
    {"nombre": "Martillo", "descripcion": "Martillo de acero", "categoria": "Herramientas", "precio_base": 5000, "stock": 20},
    {"nombre": "Destornillador", "descripcion": "Destornillador estrella", "categoria": "Herramientas", "precio_base": 2000, "stock": 50},
    {"nombre": "Taladro", "descripcion": "Taladro eléctrico", "categoria": "Eléctricas", "precio_base": 25000, "stock": 10},
]

db = SessionLocal()
for prod in productos:
    existe = db.query(Producto).filter_by(nombre=prod["nombre"]).first()
    if not existe:
        p = Producto(**prod)
        db.add(p)
db.commit()
db.close()
print("Productos cargados exitosamente en la sucursal.") 