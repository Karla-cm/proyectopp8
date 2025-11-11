
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# Configuración de la base de datos SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./estudiantes.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EstudianteDB(Base):
	__tablename__ = "estudiantes"
	id = Column(Integer, primary_key=True, index=True)
	nombre = Column(String, index=True)
	edad = Column(Integer)
	carrera = Column(String)

Base.metadata.create_all(bind=engine)

class Estudiante(BaseModel):
	id: int
	nombre: str
	edad: int
	carrera: str

@app.get("/")
async def root():
	return {"message": "API funcionando correctamente"}

# Crear estudiante
@app.post("/estudiantes/", response_model=Estudiante)
async def crear_estudiante(estudiante: Estudiante):
	db = SessionLocal()
	db_estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == estudiante.id).first()
	if db_estudiante:
		db.close()
		raise HTTPException(status_code=400, detail="El estudiante ya existe")
	nuevo = EstudianteDB(**estudiante.dict())
	db.add(nuevo)
	db.commit()
	db.refresh(nuevo)
	db.close()
	return estudiante

# Leer todos los estudiantes
@app.get("/estudiantes/", response_model=List[Estudiante])
async def leer_estudiantes():
	db = SessionLocal()
	estudiantes = db.query(EstudianteDB).all()
	db.close()
	return [Estudiante(id=e.id, nombre=e.nombre, edad=e.edad, carrera=e.carrera) for e in estudiantes]

# Leer estudiante por ID
@app.get("/estudiantes/{estudiante_id}", response_model=Estudiante)
async def leer_estudiante(estudiante_id: int):
	db = SessionLocal()
	estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == estudiante_id).first()
	db.close()
	if not estudiante:
		raise HTTPException(status_code=404, detail="Estudiante no encontrado")
	return Estudiante(id=estudiante.id, nombre=estudiante.nombre, edad=estudiante.edad, carrera=estudiante.carrera)

# Actualizar estudiante
@app.put("/estudiantes/{estudiante_id}", response_model=Estudiante)
async def actualizar_estudiante(estudiante_id: int, estudiante: Estudiante):
	db = SessionLocal()
	db_estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == estudiante_id).first()
	if not db_estudiante:
		db.close()
		raise HTTPException(status_code=404, detail="Estudiante no encontrado")
	db_estudiante.nombre = estudiante.nombre
	db_estudiante.edad = estudiante.edad
	db_estudiante.carrera = estudiante.carrera
	db.commit()
	db.refresh(db_estudiante)
	db.close()
	return estudiante

# Eliminar estudiante
@app.delete("/estudiantes/{estudiante_id}")
async def eliminar_estudiante(estudiante_id: int):
	db = SessionLocal()
	db_estudiante = db.query(EstudianteDB).filter(EstudianteDB.id == estudiante_id).first()
	if not db_estudiante:
		db.close()
		raise HTTPException(status_code=404, detail="Estudiante no encontrado")
	db.delete(db_estudiante)
	db.commit()
	db.close()
	return {"message": "Estudiante eliminado"}
#trabajr mas en los datos que quierooo