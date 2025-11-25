from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# ============================================================
# Configuración base
# ============================================================

DATABASE_URL = (
    "postgresql://base_fjwm_user:herHQfSBfoUjEITVn33ePllUToGTsMVm@dpg-d46achshg0os73eesftg-a.oregon-postgres.render.com/base_fjwm"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="API de Vinculación Laboral", version="2.0")

# ============================================================
# Carga de datos (simulando desde archivos CSV)
# ============================================================

try:
    df_vacantes = pd.read_csv('proyectopp8/ofertas_data.csv')
    df_cursos = pd.read_csv('proyectopp8/habilidades_referencia.csv') # Asumo que este es el de cursos
    VACANTES = df_vacantes.to_dict(orient='records')
    CURSOS = df_cursos.to_dict(orient='records')
except FileNotFoundError:
    VACANTES = []
    CURSOS = []

# ============================================================
# Modelos Pydantic para la nueva funcionalidad
# ============================================================

class CVInput(BaseModel):
    cv_texto: str

class CursoRecomendado(BaseModel):
    habilidad: str
    titulo_curso: str
    proveedor: str

class ResultadoMatch(BaseModel):
    vacante: Dict[str, Any]
    puntaje_match: float
    habilidades_cumplidas: List[str]
    habilidades_faltantes: List[str]
    cursos_recomendados: List[CursoRecomendado]


# ============================================================
# Funciones de NLP
# ============================================================

def normalizar_habilidad(habilidad: str) -> str:
    """Limpia la habilidad y maneja sinónimos básicos y versiones."""
    habilidad = habilidad.lower().strip()
    
    # 1. Normalizar sinónimos clave y términos compuestos
    if 'estadistica' in habilidad:
        return 'estadística'
    if 'trabajo en equipo' in habilidad or 'equipo' in habilidad:
        return 'trabajo en equipo'
    if 'resolución' in habilidad and 'problemas' in habilidad:
        return 'resolución de problemas'
    
    # 2. Manejar versiones o términos compuestos 
    terminos_clave = ['python', 'sql', 'excel', 'javascript', 'node.js', 'google ads', 'seo', 'docker', 'liderazgo']
    for termino in terminos_clave:
        if termino in habilidad:
            return termino
            
    return habilidad

def extraer_habilidades(cv_texto: str, lista_habilidades_conocidas: set) -> set:
    """Procesa el texto del CV y busca coincidencias con las habilidades conocidas."""
    habilidades_encontradas = set()
    habilidades_normalizadas = {normalizar_habilidad(h) for h in lista_habilidades_conocidas}
    cv_texto_limpio = normalizar_habilidad(cv_texto)
    
    for habilidad in habilidades_normalizadas:
        if habilidad in cv_texto_limpio:
            habilidades_encontradas.add(habilidad)
            
    return habilidades_encontradas

def calcular_similitud_tfidf(cv_texto: str, vacantes: List[Dict[str, Any]]) -> Dict[int, float]:
    """Calcula la similitud coseno entre el texto del CV y la descripción de cada vacante."""
    descripciones = [v.get('Descripcion_Puesto', '') for v in vacantes]
    documentos = [cv_texto] + descripciones
    
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True) 
    tfidf_matrix = vectorizer.fit_transform(documentos)
    
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    scores = cosine_sim[0]
    
    return {vacantes[i]['ID_Oferta']: score for i, score in enumerate(scores)}

# ============================================================
# Rutas de la API
# ============================================================

@app.get("/")
async def root():
    return {"message": "✅ API de Vinculación Laboral funcionando correctamente"}

@app.post("/match-jobs/", response_model=List[ResultadoMatch])
async def encontrar_trabajos_compatibles(cv_input: CVInput):
    """
    Recibe el texto de un CV y devuelve una lista de vacantes ordenadas por compatibilidad.
    """
    cv_texto = cv_input.cv_texto
    if not cv_texto or not cv_texto.strip():
        raise HTTPException(status_code=400, detail="El 'cv_texto' no puede estar vacío.")

    if not VACANTES:
        return []

    # 1. Extraer todas las habilidades únicas de las vacantes
    todas_habilidades = set()
    for v in VACANTES:
        todas_habilidades.update([h.strip() for h in v.get('Req_Hard_Skills', '').split(',')])
        todas_habilidades.update([h.strip() for h in v.get('Req_Soft_Skills', '').split(',')])

    # 2. Procesar el CV
    habilidades_cv = extraer_habilidades(cv_texto, todas_habilidades)
    tfidf_scores = calcular_similitud_tfidf(cv_texto, VACANTES) 

    # 3. Calcular compatibilidad para cada vacante
    resultados = []
    for vacante in VACANTES:
        req_tec = {normalizar_habilidad(h) for h in vacante.get('Req_Hard_Skills', '').split(',')}
        req_blando = {normalizar_habilidad(h) for h in vacante.get('Req_Soft_Skills', '').split(',')}
        req_totales = req_tec.union(req_blando)
        
        habilidades_cumplidas = habilidades_cv.intersection(req_totales)
        habilidades_faltantes = req_totales - habilidades_cv

        # Cálculo del Score FINAL
        score_cumplimiento = len(habilidades_cumplidas) / len(req_totales) if req_totales else 0
        score_relevancia = tfidf_scores.get(vacante['ID_Oferta'], 0)
        puntaje_final = (score_cumplimiento * 0.6) + (score_relevancia * 0.4)
        
        # 4. Recomendación de Cursos
        cursos_recomendados = [
            curso for curso in CURSOS 
            if normalizar_habilidad(curso['habilidad']) in habilidades_faltantes
        ]

        resultados.append({
            "vacante": vacante,
            "puntaje_match": round(puntaje_final * 100, 2),
            "habilidades_cumplidas": list(habilidades_cumplidas),
            "habilidades_faltantes": list(habilidades_faltantes),
            "cursos_recomendados": cursos_recomendados
        })

    # 5. Ordenar resultados por mejor match
    resultados_ordenados = sorted(resultados, key=lambda x: x['puntaje_match'], reverse=True)
    
    return resultados_ordenados
