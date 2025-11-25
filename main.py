from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ============================================================
# Configuración base
# ============================================================

DATABASE_URL = (
    "postgresql://base_fjwm_user:herHQfSBfoUjEITVn33ePllUToGTsMVm@dpg-d46achshg0os73eesftg-a.oregon-postgres.render.com/base_fjwm"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="API de Estudiantes", version="1.0")

# ============================================================
# Modelo de Base de Datos
# ============================================================

class EstudianteDB(Base):
    __tablename__ = "estudiantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    edad = Column(Integer)
    carrera = Column(String)

Base.metadata.create_all(bind=engine)

# ============================================================
# Modelo Pydantic
# ============================================================

class Estudiante(BaseModel):
    id: int
    nombre: str
    edad: int
    carrera: str

    model_config = {
        "from_attributes": True  # permite convertir objetos SQLAlchemy en JSON fácilmente
    }

# ============================================================
# Dependencia para obtener sesión
# ============================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# Rutas
# ============================================================

@app.get("/")
async def root():
    return {"message": "✅ API funcionando correctamente"}


# Crear estudiante
@app.post("/estudiantes/", response_model=Estudiante)
async def crear_estudiante(estudiante: Estudiante, db: Session = Depends(get_db)):
    if db.query(EstudianteDB).filter(EstudianteDB.id == estudiante.id).first():
        raise HTTPException(status_code=400, detail="El estudiante ya existe")

    nuevo = EstudianteDB(**estudiante.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# Leer todos los estudiantes
@app.get("/estudiantes/", response_model=List[Estudiante])
async def leer_estudiantes(db: Session = Depends(get_db)):
    return db.query(EstudianteDB).all()


# Leer estudiante por ID
@app.get("/estudiantes/{estudiante_id}", response_model=Estudiante)
async def leer_estudiante(estudiante_id: int, db: Session = Depends(get_db)):
    estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == estudiante_id).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante


# Actualizar estudiante
@app.put("/estudiantes/{estudiante_id}", response_model=Estudiante)
async def actualizar_estudiante(estudiante_id: int, estudiante: Estudiante, db: Session = Depends(get_db)):
    db_estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == estudiante_id).first()
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    for key, value in estudiante.dict().items():
        setattr(db_estudiante, key, value)

    db.commit()
    db.refresh(db_estudiante)
    return db_estudiante


# Eliminar estudiante
@app.delete("/estudiantes/{estudiante_id}")
async def eliminar_estudiante(estudiante_id: int, db: Session = Depends(get_db)):
    db_estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == estudiante_id).first()
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    db.delete(db_estudiante)
    db.commit()
    return {"message": f"Estudiante con ID {estudiante_id} eliminado correctamente"}


# ============================================================
# Prueba de conexión
# ============================================================

if __name__ == "__main__":
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).fetchone()
            print(f"✅ Conexión exitosa a PostgreSQL. Versión: {version[0]}")
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
