from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple
from textwrap import dedent
import streamlit as st
import pandas as pd
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ===============================
# 📌 MODELOS DE DATOS
# ===============================

@dataclass
class ExperienciaLaboral:
    """Representa una experiencia laboral en el perfil de un candidato."""
    puesto: str
    empresa: str
    descripcion: str
    fecha_inicio: date
    fecha_fin: Optional[date] = None  # None si es el trabajo actual

    def __str__(self) -> str:
        fecha_fin_str = self.fecha_fin.strftime("%B %Y") if self.fecha_fin else "Actualidad"
        return (
            f"- Puesto: {self.puesto} en {self.empresa} "
            f"({self.fecha_inicio.strftime('%B %Y')} - {fecha_fin_str})\n"
            f"  Descripción: {self.descripcion}"
        )


@dataclass
class OfertaDeTrabajo:
    """Modela una oferta de trabajo con sus requisitos."""
    puesto: str
    empresa: str
    habilidades_requeridas: List[str] = field(default_factory=list)
    experiencia_minima_meses: int = 0


@dataclass
class PerfilCandidato:
    """Modela el perfil de un candidato en la plataforma."""
    nombre: str
    email: str
    telefono: Optional[str] = None
    resumen_profesional: str = ""
    habilidades: List[str] = field(default_factory=list)
    experiencias: List[ExperienciaLaboral] = field(default_factory=list)

    # -------------------------------
    # 🔹 MÉTODOS DE UTILIDAD
    # -------------------------------

    def get_experiencia_total_meses(self) -> int:
        """Calcula los meses totales de experiencia del candidato."""
        hoy = date.today()
        total_meses = 0
        for exp in self.experiencias:
            fecha_fin = exp.fecha_fin or hoy
            total_meses += (fecha_fin.year - exp.fecha_inicio.year) * 12 + (fecha_fin.month - exp.fecha_inicio.month)
        return total_meses

    def get_habilidades_normalizadas(self) -> List[str]:
        """Devuelve las habilidades en minúsculas para comparación."""
        return [h.lower() for h in self.habilidades]

    def agregar_habilidad(self, habilidad: str) -> None:
        """Agrega una habilidad si no existe (ignorando mayúsculas/minúsculas)."""
        if habilidad.lower() not in [h.lower() for h in self.habilidades]:
            self.habilidades.append(habilidad)

    def agregar_experiencia(self, experiencia: ExperienciaLaboral) -> None:
        """Agrega una experiencia laboral al perfil, ordenada por fecha."""
        self.experiencias.append(experiencia)
        self.experiencias.sort(key=lambda exp: exp.fecha_inicio, reverse=True)

    # -------------------------------
    # 🔹 FORMATOS DE SALIDA
    # -------------------------------

    def generar_html(self) -> str:
        """Genera una representación en HTML del perfil completo del candidato."""
        habilidades_html = (
            "".join(f"<span>{h}</span>" for h in sorted(self.habilidades, key=str.lower))
            if self.habilidades else "<p>No hay habilidades registradas.</p>"
        )

        experiencias_html = (
            "".join(
                f"""
                <div class="experiencia">
                    <h3>{exp.puesto}</h3>
                    <h4>{exp.empresa} | {exp.fecha_inicio.strftime('%B %Y')} - {exp.fecha_fin.strftime('%B %Y') if exp.fecha_fin else 'Actualidad'}</h4>
                    <p>{exp.descripcion}</p>
                </div>
                """ for exp in self.experiencias
            ) if self.experiencias else "<p>No hay experiencia laboral registrada.</p>"
        )

        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Perfil de {self.nombre}</title>
            <link rel="stylesheet" href="estilos.css">
            <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap" rel="stylesheet">
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h1>{self.nombre}</h1>
                    <p class="contacto">
                        <a href="mailto:{self.email}">{self.email}</a>
                        {' | ' + self.telefono if self.telefono else ''}
                    </p>
                </div>
                <div class="seccion">
                    <h2>Resumen Profesional</h2>
                    <p>{self.resumen_profesional}</p>
                </div>
                <div class="seccion">
                    <h2>Habilidades</h2>
                    <div class="habilidades-container">{habilidades_html}</div>
                </div>
                <div class="seccion">
                    <h2>Experiencia Laboral</h2>
                    {experiencias_html}
                </div>
            </div>
        </body>
        </html>
        """

    def mostrar_perfil(self) -> str:
        """Devuelve una representación en texto del perfil completo."""
        perfil_str = f"Perfil de: {self.nombre}\nEmail: {self.email}\n"
        if self.telefono:
            perfil_str += f"Teléfono: {self.telefono}\n"
        perfil_str += f"\n--- Resumen Profesional ---\n{self.resumen_profesional}\n"

        perfil_str += "\n--- Habilidades ---\n"
        perfil_str += "- " + "\n- ".join(sorted(self.habilidades, key=str.lower)) if self.habilidades else "No hay habilidades registradas."

        perfil_str += "\n\n--- Experiencia Laboral ---\n"
        perfil_str += "\n".join(str(exp) for exp in self.experiencias) if self.experiencias else "No hay experiencia laboral registrada."
        return perfil_str


# ===============================
# 🌐 CONFIGURACIÓN FLASK Y DATOS GLOBALES
# ===============================
app = Flask(__name__)
CORS(app)

VACANTES: List[dict] = []
CURSOS: List[dict] = []

def _load_global_data():
    """
    Carga y prepara los datos de vacantes y cursos a nivel global
    para ser usados tanto por la aplicación Streamlit como por la API Flask.
    """
    global VACANTES, CURSOS

    try:
        # Intentar cargar desde archivos JSON
        with open('vacantes.json', 'r', encoding='utf-8') as f:
            VACANTES = json.load(f)
        
        with open('cursos.json', 'r', encoding='utf-8') as f:
            CURSOS = json.load(f)
    except FileNotFoundError:
        # Fallback a datos de ejemplo si no hay archivos
        VACANTES = [
            {
                "id": 1,
                "titulo": "Desarrollador Python",
                "empresa": "Tech Solutions",
                "descripcion": "Desarrollo de aplicaciones web con Python y Django",
                "requisitos_tecnicos": ["Python", "Django", "SQL"],
                "requisitos_blandos": ["Trabajo en equipo", "Comunicación"]
            }
        ]
        
        CURSOS = [
            {"habilidad": "Python", "titulo_curso": "Curso intensivo de Python para Data Science", "proveedor": "Coursera"},
            {"habilidad": "SQL", "titulo_curso": "Introducción a Bases de Datos Relacionales (SQL)", "proveedor": "edX"},
            {"habilidad": "Trabajo en equipo", "titulo_curso": "Taller de Liderazgo y Colaboración Efectiva", "proveedor": "LinkedIn Learning"},
            {"habilidad": "Creatividad", "titulo_curso": "Desarrollo del Pensamiento Creativo Aplicado", "proveedor": "Platzi"}
        ]

# Cargar los datos globales al inicio del script
_load_global_data()


# ===============================
# 📊 FUNCIONES DE ANÁLISIS
# ===============================

def verificar_compatibilidad(perfil: PerfilCandidato, oferta: OfertaDeTrabajo) -> Tuple[int, List[str], List[str]]:
    """Compara un perfil con una oferta y devuelve compatibilidad y detalles."""
    habilidades_candidato = perfil.get_habilidades_normalizadas()
    habilidades_oferta = [h.lower() for h in oferta.habilidades_requeridas]

    coincidentes = list(set(habilidades_candidato) & set(habilidades_oferta))
    faltantes = list(set(habilidades_oferta) - set(habilidades_candidato))

    score = (len(coincidentes) / len(habilidades_oferta) * 100) if habilidades_oferta else 100
    return int(score), coincidentes, faltantes


# ===============================
# 🧠 FUNCIONES NLP
# ===============================

def normalizar_habilidad(habilidad):
    """Limpia la habilidad y maneja sinónimos básicos y versiones."""
    habilidad = habilidad.lower().strip()
    if 'estadistica' in habilidad:
        return 'estadística'
    if 'trabajo en equipo' in habilidad or 'equipo' in habilidad:
        return 'trabajo en equipo'
    if 'resolución' in habilidad and 'problemas' in habilidad:
        return 'resolución de problemas'
    terminos_clave = ['python', 'sql', 'excel', 'javascript', 'node.js', 'google ads', 'seo', 'docker', 'liderazgo']
    for termino in terminos_clave:
        if termino in habilidad:
            return termino
    return habilidad

def extraer_habilidades(cv_texto, lista_habilidades_conocidas):
    """Procesa el texto del CV y busca coincidencias con las habilidades conocidas."""
    habilidades_encontradas = set()
    habilidades_normalizadas = [normalizar_habilidad(h) for h in lista_habilidades_conocidas]
    cv_texto_limpio = normalizar_habilidad(cv_texto)
    for habilidad in habilidades_normalizadas:
        if habilidad in cv_texto_limpio:
            habilidades_encontradas.add(habilidad)
    return habilidades_encontradas

def calcular_similitud_tfidf(cv_texto, vacantes):
    """Calcula la similitud coseno entre el texto del CV y la descripción de cada vacante."""
    documentos = [cv_texto] + [v['descripcion'] for v in vacantes]
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
    tfidf_matrix = vectorizer.fit_transform(documentos)
    cosine_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:])
    scores = cosine_sim[0]
    tfidf_scores = {}
    for i, score in enumerate(scores):
        vacante_id = vacantes[i]['id']
        tfidf_scores[vacante_id] = score
    return tfidf_scores


# ===============================
# 🚀 ENDPOINTS DE LA API FLASK
# ===============================

@app.route('/aplicar', methods=['POST'])
def aplicar_vacante():
    """Recibe el texto del CV, hace el match con dos modelos y devuelve recomendaciones."""
    data = request.json
    cv_texto = data.get('cv_texto', '')

    if not cv_texto:
        return jsonify({"error": "No se proporcionó texto de CV"}), 400

    resultados = []
    todas_habilidades = set()
    for v in VACANTES:
        todas_habilidades.update(v['requisitos_tecnicos'])
        todas_habilidades.update(v['requisitos_blandos'])

    habilidades_cv = extraer_habilidades(cv_texto, todas_habilidades)
    tfidf_scores = calcular_similitud_tfidf(cv_texto, VACANTES)

    for vacante in VACANTES:
        req_tec = set(normalizar_habilidad(h) for h in vacante['requisitos_tecnicos'])
        req_blando = set(normalizar_habilidad(h) for h in vacante['requisitos_blandos'])
        req_totales = req_tec.union(req_blando)

        habilidades_cumplidas = habilidades_cv.intersection(req_totales)
        habilidades_faltantes = req_totales - habilidades_cv

        total_req = len(req_totales)
        score_cumplimiento = len(habilidades_cumplidas) / total_req if total_req else 0

        score_relevancia = tfidf_scores.get(vacante['id'], 0)
        puntaje_final = (score_cumplimiento * 0.6) + (score_relevancia * 0.4) # ponderación de 60/40

        cursos_recomendados = [
            curso for curso in CURSOS
            if normalizar_habilidad(curso['habilidad']) in habilidades_faltantes
        ]

        resultados.append({
            "vacante_id": vacante['id'],
            "titulo": vacante['titulo'],
            "empresa": vacante['empresa'],
            "puntaje_match": round(puntaje_final * 100, 2),
            "habilidades_cumplidas": list(habilidades_cumplidas),
            "habilidades_faltantes": list(habilidades_faltantes),
            "cursos_recomendados": cursos_recomendados
        })

    resultados_ordenados = sorted(resultados, key=lambda x: x['puntaje_match'], reverse=True)

    return jsonify(resultados_ordenados)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que la API está funcionando."""
    return jsonify({
        "status": "ok", 
        "message": "API CogniLink funcionando correctamente",
        "vacantes_cargadas": len(VACANTES),
        "cursos_cargados": len(CURSOS)
    })


# ===============================
# 🎯 APLICACIÓN STREAMLIT
# ===============================

def run_streamlit_app():
    """Ejecuta la aplicación Streamlit principal."""
    
    # Configuración de página
    st.set_page_config(page_title="CogniLink UNRC", layout="wide")

    # Estilos CSS personalizados
    st.markdown("""
    <style>
    body { background-color: #f5faff; }
    .main-card {
        background: linear-gradient(90deg, #0a1f2e 60%, #00e6e6 100%);
        border-radius: 20px;
        box-shadow: 0 4px 24px #0a1f2e22;
        padding: 2.5rem;
        margin-top: 2rem;
        color: #fff;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }
    .main-card h1 {
        color: #00e6e6;
        margin-bottom: 0.5rem;
        font-size: 2.5rem;
    }
    .main-card img {
        height: 60px;
        margin-bottom: 1rem;
    }
    .stTextInput>div>input {
        border-radius: 8px;
        border: 2px solid #00e6e6;
        padding: 0.7rem 1rem;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: #00e6e6;
        color: #0a1f2e;
        border-radius: 8px;
        border: none;
        padding: 0.7rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        margin-top: 1rem;
        box-shadow: 0 2px 8px #00e6e633;
        transition: background 0.2s, color 0.2s;
    }
    .stButton>button:hover {
        background: #0a1f2e;
        color: #00e6e6;
    }
    .result-card {
        background: #fff;
        border-radius: 16px;
        box-shadow: 0 4px 24px #0a1f2e22;
        padding: 2rem;
        margin-top: 2rem;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
    }
    .skill-match { background: #00e6e6; color: #0a1f2e; border-radius: 6px; padding: 0.3rem 0.8rem; margin: 0.2rem; display: inline-block; font-weight: 500; }
    .skill-missing { background: #ffe6e6; color: #cc0000; border-radius: 6px; padding: 0.3rem 0.8rem; margin: 0.2rem; display: inline-block; font-weight: 500; }
    .course-card { background: #e6f7ff; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; border-left: 6px solid #00e6e6; }
    </style>
    """, unsafe_allow_html=True)

    # Header principal
    st.markdown("""
    <div class='main-card'>
        <img src='https://files.oaiusercontent.com/file-7b2b6e2e-7e2e-4e2e-8e2e-7e2e7e2e7e2e/imagen.png'>
        <h1>CogniLink UNRC</h1>
        <p style='font-size:1.2rem;'>Sistema inteligente de vinculación laboral para egresados UNRC.<br>Ingresa tu <b>ID de egresado</b> y tu contraseña para ver tu perfil profesional y ofertas relacionadas.</p>
    </div>
    """, unsafe_allow_html=True)

    # Formulario de login
    with st.form("login_form"):
        id_input = st.text_input("ID de egresado", max_chars=10)
        password_input = st.text_input("Ingresa tu contraseña", type="password")
        login_btn = st.form_submit_button("Ingresar")

    # Cargar datos de ejemplo (en un caso real, esto vendría de una base de datos)
    try:
        from db_utils import cargar_tabla
        df_egresados = cargar_tabla('egresados')
        df_ofertas = cargar_tabla('ofertas')
        df_habilidades = cargar_tabla('habilidades')
    except ImportError:
        # Datos de ejemplo si no hay db_utils
        df_egresados = pd.DataFrame([{
            'ID_Egresado': '123',
            'Nombre': 'Juan Pérez',
            'Anio_Egreso': 2020,
            'Rol_Deseado': 'Desarrollador Python',
            'Experiencia_Anios': 3,
            'Hard_Skills': 'Python, SQL, Django',
            'Soft_Skills': 'Trabajo en equipo, Comunicación',
            'Resumen_CV': 'Desarrollador con experiencia en aplicaciones web'
        }])
        df_ofertas = pd.DataFrame([{
            'Puesto': 'Desarrollador Python',
            'Empresa': 'Tech Solutions',
            'Min_Exp_Anios': 2,
            'Req_Hard_Skills': 'Python, Django, SQL',
            'Req_Soft_Skills': 'Trabajo en equipo',
            'Descripcion_Puesto': 'Desarrollo de aplicaciones web con Python'
        }])

    if login_btn:
        # Validar credenciales
        egresado = df_egresados[df_egresados['ID_Egresado'].astype(str) == id_input]
        
        if not egresado.empty and egresado.iloc[0]['Nombre'].strip().lower() == password_input.strip().lower():
            st.success(f"Bienvenido/a, {egresado.iloc[0]['Nombre']}!")
            
            # Mostrar perfil del egresado
            st.markdown(f"""
            <div class='result-card'>
                <div style='display: flex; align-items: center;'>
                    <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='48' style='margin-right: 16px;'>
                    <h3 style='color:#00e6e6; margin-bottom:0;'>Perfil del Egresado</h3>
                </div>
                <hr>
                <b>ID:</b> {id_input}<br>
                <b>Nombre:</b> {egresado.iloc[0]['Nombre']}<br>
                <b>Año de Egreso:</b> {egresado.iloc[0]['Anio_Egreso']}<br>
                <b>Rol Deseado:</b> {egresado.iloc[0]['Rol_Deseado']}<br>
                <b>Experiencia (años):</b> {egresado.iloc[0]['Experiencia_Anios']}<br>
            </div>
            """, unsafe_allow_html=True)

            # Mostrar habilidades
            hard_skills = [h.strip() for h in egresado.iloc[0]['Hard_Skills'].split(',')]
            soft_skills = [s.strip() for s in egresado.iloc[0]['Soft_Skills'].split(',')]
            
            st.markdown("<b>Hard Skills:</b>", unsafe_allow_html=True)
            st.markdown(' '.join([f"<span class='skill-match'>{skill}</span>" for skill in hard_skills]), unsafe_allow_html=True)

            st.markdown("<b>Soft Skills:</b>", unsafe_allow_html=True)
            st.markdown(' '.join([f"<span class='skill-match'>{skill}</span>" for skill in soft_skills]), unsafe_allow_html=True)

            st.markdown(f"<b>Resumen CV:</b> {egresado.iloc[0]['Resumen_CV']}", unsafe_allow_html=True)

            # --- Matching Inteligente de Vacantes y Cursos ---
            st.markdown("<hr><h4 style='color:#00e6e6;'>Matching Inteligente de Vacantes y Cursos</h4>", unsafe_allow_html=True)
            st.info("Pega el texto de tu CV para recibir recomendaciones personalizadas de vacantes y cursos.")
            
            cv_texto = st.text_area("Pega aquí el texto de tu CV para analizar tu perfil y recomendarte vacantes y cursos:")

            if st.button("Analizar y Recomendar"):
                if not cv_texto.strip():
                    st.error("Debes ingresar el texto de tu CV.")
                else:
                    # Simular llamada a la API Flask
                    resultados = []
                    todas_habilidades = set()
                    for v in VACANTES:
                        todas_habilidades.update(v['requisitos_tecnicos'])
                        todas_habilidades.update(v['requisitos_blandos'])
                    
                    habilidades_cv = extraer_habilidades(cv_texto, todas_habilidades)
                    tfidf_scores = calcular_similitud_tfidf(cv_texto, VACANTES)
                    
                    for vacante in VACANTES:
                        req_tec = set(normalizar_habilidad(h) for h in vacante['requisitos_tecnicos'])
                        req_blando = set(normalizar_habilidad(h) for h in vacante['requisitos_blandos'])
                        req_totales = req_tec.union(req_blando)
                        
                        habilidades_cumplidas = habilidades_cv.intersection(req_totales)
                        habilidades_faltantes = req_totales - habilidades_cv
                        
                        total_req = len(req_totales)
                        score_cumplimiento = len(habilidades_cumplidas) / total_req if total_req else 0
                        score_relevancia = tfidf_scores.get(vacante['id'], 0)
                        puntaje_final = (score_cumplimiento * 0.6) + (score_relevancia * 0.4)
                        
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
                    
                    resultados_ordenados = sorted(resultados, key=lambda x: x['puntaje_match'], reverse=True)
                    
                    # Mostrar resultados
                    for res in resultados_ordenados:
                        v = res["vacante"]
                        st.markdown(f"""
                        <div class='result-card'>
                            <h3>{v['titulo']} ({v['empresa']})</h3>
                            <p><b>Puntaje de match:</b> {res['puntaje_match']}%</p>
                            <p><b>Habilidades cumplidas:</b> {', '.join(res['habilidades_cumplidas'])}</p>
                            <p><b>Habilidades faltantes:</b> {', '.join(res['habilidades_faltantes'])}</p>
                            <p><b>Cursos recomendados:</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for curso in res["cursos_recomendados"]:
                            st.markdown(f"""
                            <div class='course-card'>
                                <b>{curso['titulo_curso']}</b> ({curso['proveedor']})<br>
                                <i>Habilidad objetivo: {curso['habilidad']}</i>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")

        else:
            st.error("ID o nombre incorrecto. Por favor, verifica tus datos.")


# ===============================
# 🚀 PUNTO DE ENTRADA PRINCIPAL
# ===============================

if __name__ == "__main__":
    import sys
    
    # Determinar si ejecutar Flask o Streamlit
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("🚀 Iniciando API Flask en http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("🎯 Iniciando aplicación Streamlit")
        run_streamlit_app()