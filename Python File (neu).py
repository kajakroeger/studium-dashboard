"""
SQLAlchemy-Definition der Datenbank-Tabellen für das Studium-Dashboard.
Jede Klasse entspricht einer Tabelle. Beziehungen werden über Foreign Keys hergestellt.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# Tabelle Kurs
class Kurs(Base):
    __tablename__ = "kurs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    ects = Column(Integer, nullable=False)
    note = Column(Float)

    # Beziehung: ein Kurs hat viele Bearbeitungen
    bearbeitungen = relationship("Bearbeitung", back_populates="kurs")

    def __repr__(self):
        return f"<Kurs(name={self.name}, ects={self.ects}, note={self.note})>"


# Tabelle Bearbeitung
class Bearbeitung(Base):
    __tablename__ = "bearbeitung"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kurs_id = Column(Integer, ForeignKey("kurs.id"), nullable=False)
    start_datum = Column(Date)
    abgabe_datum = Column(Date)
    status = Column(String)

    # Beziehung: Bearbeitung gehört zu einem Kurs
    kurs = relationship("Kurs", back_populates="bearbeitungen")

    def __repr__(self):
        return f"<Bearbeitung(kurs_id={self.kurs_id}, status={self.status})>"


# Datenbank erstellen (SQLite)
engine = create_engine("sqlite:///studium.db")
Base.metadata.create_all(engine)

# Session für Inserts / Queries
Session = sessionmaker(bind=engine)
session = Session()

# Beispiel: Testdaten einfügen
kurs1 = Kurs(name="Programmierung", ects=5, note=1.7)
bearbeitung1 = Bearbeitung(start_datum="2025-01-05", abgabe_datum="2025-02-02", status="abgeschlossen", kurs=kurs1)

session.add(kurs1)
session.add(bearbeitung1)
session.commit()
