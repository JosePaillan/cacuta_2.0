from sqlalchemy import Column, Integer, String, Float, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    precio_base = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False, comment="Stock disponible en la sucursal")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('precio_base > 0', name='check_precio_base_positive'),
        CheckConstraint('stock >= 0', name='check_stock_non_negative'),
    )
