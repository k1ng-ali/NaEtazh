"""
Модели адресов доставки.

- ResidentialComplex: жилой комплекс
- Building: корпус, code используется в ссылке QR-кода
"""

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, Integer, String, func

from app.core.database import Base


class ResidentialComplex(Base):
    __tablename__ = "residential_complexes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class Building(Base):
    __tablename__ = "buildings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    complex_id = Column(
        BigInteger,
        ForeignKey("residential_complexes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    floors = Column(Integer, nullable=True)
    # Что может поместиться в лифт, для предупреждения о длинных материалах
    cargo_lift_length_mm = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
