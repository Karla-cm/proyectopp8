import streamlit as st
from db_utils import cargar_tabla
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# ===============================
# 📌 CONFIGURACIÓN DE LA PÁGINA
# ===============================

st.set_page_config(page_title="CogniLink UNRC", layout="wide")

# --- CARGA CSS ---
def load_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css('estilos.css')

# ===============================
#  trạng thái phiên (SESSION STATE)
# ===============================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.egresado = None

# ===============================
# 📊 FUNCIONES DE ANÁLISIS
# ===============================

def normalizar_habilidad(habilidad):
    habilidad = habilidad.lower().strip()
    sinonimos = {
        'estadistica': 'estadística',
        'trabajo en equipo': 'trabajo en equipo',
        'equipo': 'trabajo en equipo',
        'resolución de problemas': 'resolución de problemas',
        'resolucion': 'resolución de problemas',
    }
    if habilidad in sinonimos:
        return sinonimos[habilidad]

    terminos_clave = ['python', 'sql', 'excel', 'javascript', 'node.js', 'google ads', 'seo', 'docker', 'liderazgo']
    for termino in terminos_clave:
        if termino in habilidad:
            return termino
            
    return habilidad

def extraer_habilidades(cv_texto, lista_habilidades_conocidas):
    habilidades_encontradas = set()
    habilidades_normalizadas = {normalizar_habilidad(h) for h in lista_habilidades_conocidas}
    cv_texto_limpio = normalizar_habilidad(cv_texto)
    
    for habilidad in habilidades_normalizadas:
        if habilidad in cv_texto_limpio:
            habilidades_encontradas.add(habilidad)
            
    return habilidades_encontradas

def calcular_similitud_tfidf(cv_texto, vacantes):
    documentos = [cv_texto] + [v['descripcion'] for v in vacantes]
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True) 
    tfidf_matrix = vectorizer.fit_transform(documentos)
    cosine_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:])
    scores = cosine_sim[0]
    
    return {vacantes[i]['id']: score for i, score in enumerate(scores)}

# ===============================
# 🚪 PÁGINA DE LOGIN
# ===============================

if not st.session_state.logged_in:
    st.markdown("""
    <div class='login-card'>
        <img src='image/Captura de pantalla 2025-11-21 041023.png' style='height: 80px; margin-bottom: 1rem;'>
        <h1>Bienvenido a CogniLink</h1>
        <p class='subtitle'>Tu portal de vinculación laboral inteligente en la UNRC.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        id_input = st.text_input("ID de egresado", max_chars=10)
        password_input = st.text_input("Ingresa tu contraseña", type="password")
        login_btn = st.form_submit_button("Ingresar")

        if login_btn:
            df_egresados = cargar_tabla('egresados')
            egresado = df_egresados[df_egresados['ID_Egresado'].astype(str) == id_input]
            
            if not egresado.empty and egresado.iloc[0]['Nombre'].strip().lower() == password_input.strip().lower():
                st.session_state.logged_in = True
                st.session_state.egresado = egresado.iloc[0]
                st.rerun()
            else:
                st.error("ID o contraseña incorrectos. Por favor, verifica tus datos.")

# ===============================
# 🏠 PÁGINA PRINCIPAL
# ===============================

else:
    egresado = st.session_state.egresado

    # --- BARRA SUPERIOR ---
    st.markdown("""
    <div class='topbar'>
        <div class='logo'>
            <img src='https://files.oaiusercontent.com/file-7b2b6e2e-7e2e-4e2e-8e2e-7e2e7e2e7e2e/imagen.png' alt='CogniLink Logo'>
            CogniLink UNRC
        </div>
        <div class='user-info'>
            <span>Bienvenido/a, <b>{nombre}</b></span>
        </div>
    </div>
    """.format(nombre=egresado['Nombre']), unsafe_allow_html=True)

    st.markdown("---")

    # --- PERFIL DEL EGRESADO ---
    st.markdown("### Perfil del Egresado")
    st.markdown(f"""
    <div class='profile-card'>
        <div class='profile-header'>
            <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' class='profile-icon'>
            <div>
                <h4>{egresado['Nombre']}</h4>
                <p>ID: {egresado['ID_Egresado']} | Año de Egreso: {egresado['Anio_Egreso']}</p>
            </div>
        </div>
        <p><b>Rol Deseado:</b> {egresado['Rol_Deseado']}</p>
        <p><b>Experiencia:</b> {egresado['Experiencia_Anios']} años</p>
        <p><b>Resumen CV:</b> {egresado['Resumen_CV']}</p>
        
        <h5>Hard Skills</h5>
        <div>
            {''.join(f"<span class='skill-tag hard-skill'>{skill.strip()}</span>" for skill in egresado['Hard_Skills'].split(','))}
        </div>
        <h5 style='margin-top: 1rem;'>Soft Skills</h5>
        <div>
            {''.join(f"<span class='skill-tag soft-skill'>{skill.strip()}</span>" for skill in egresado['Soft_Skills'].split(','))}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- MATCHING INTELIGENTE ---
    st.markdown("### Matching Inteligente de Vacantes y Cursos")
    st.info("Pega el texto de tu CV para recibir recomendaciones personalizadas.")

    cv_texto = st.text_area("Pega aquí el texto de tu CV:", height=200)

    if st.button("Analizar y Recomendar"):
        if not cv_texto.strip():
            st.error("Debes ingresar el texto de tu CV.")
        else:
            with st.spinner("Analizando tu perfil..."):
                # Cargar datos
                df_vacantes = cargar_tabla('ofertas')
                df_cursos = pd.DataFrame([
                    {"habilidad": "Python", "titulo_curso": "Curso de Python para Data Science", "proveedor": "Coursera"},
                    {"habilidad": "SQL", "titulo_curso": "SQL para Análisis de Datos", "proveedor": "edX"},
                    {"habilidad": "Trabajo en equipo", "titulo_curso": "Colaboración Efectiva en Equipos", "proveedor": "LinkedIn Learning"},
                ])
                
                VACANTES = [{
                    "id": row["ID_Oferta"], "titulo": row["Puesto"], "empresa": row["Empresa"],
                    "descripcion": row["Descripcion_Puesto"],
                    "requisitos_tecnicos": [h.strip() for h in row["Req_Hard_Skills"].split(",")],
                    "requisitos_blandos": [h.strip() for h in row["Req_Soft_Skills"].split(",")]
                } for _, row in df_vacantes.iterrows()]
                CURSOS = df_cursos.to_dict(orient="records")

                # Procesamiento
                todas_habilidades = {h for v in VACANTES for h in v['requisitos_tecnicos'] + v['requisitos_blandos']}
                habilidades_cv = extraer_habilidades(cv_texto, todas_habilidades)
                tfidf_scores = calcular_similitud_tfidf(cv_texto, VACANTES)
                
                resultados = []
                for vacante in VACANTES:
                    req_tec = {normalizar_habilidad(h) for h in vacante['requisitos_tecnicos']}
                    req_blando = {normalizar_habilidad(h) for h in vacante['requisitos_blandos']}
                    req_totales = req_tec.union(req_blando)
                    
                    habilidades_cumplidas = habilidades_cv.intersection(req_totales)
                    habilidades_faltantes = req_totales - habilidades_cv
                    
                    score_cumplimiento = len(habilidades_cumplidas) / len(req_totales) if req_totales else 0
                    score_relevancia = tfidf_scores.get(vacante['id'], 0)
                    puntaje_final = (score_cumplimiento * 0.6) + (score_relevancia * 0.4)
                    
                    cursos_recomendados = [c for c in CURSOS if normalizar_habilidad(c['habilidad']) in habilidades_faltantes]

                    resultados.append({
                        "vacante": vacante,
                        "puntaje_match": round(puntaje_final * 100, 2),
                        "habilidades_cumplidas": list(habilidades_cumplidas),
                        "habilidades_faltantes": list(habilidades_faltantes),
                        "cursos_recomendados": cursos_recomendados
                    })
                
                resultados_ordenados = sorted(resultados, key=lambda x: x['puntaje_match'], reverse=True)

                st.markdown("---")
                st.markdown("#### Resultados del Análisis")

                for res in resultados_ordenados:
                    v = res['vacante']
                    with st.expander(f"{v['titulo']} en {v['empresa']} - {res['puntaje_match']}% Match"):
                        st.markdown(f"<h6>Habilidades Cumplidas</h6>", unsafe_allow_html=True)
                        st.markdown(' '.join(f"<span class='skill-tag-small hard-skill'>{h}</span>" for h in res['habilidades_cumplidas']), unsafe_allow_html=True)
                        
                        st.markdown(f"<h6>Habilidades Faltantes</h6>", unsafe_allow_html=True)
                        st.markdown(' '.join(f"<span class='skill-tag-small missing'>{h}</span>" for h in res['habilidades_faltantes']), unsafe_allow_html=True)
                        
                        if res['cursos_recomendados']:
                            st.markdown("<h6>Cursos Recomendados para Reducir la Brecha</h6>", unsafe_allow_html=True)
                            for curso in res['cursos_recomendados']:
                                st.write(f"▶️ **{curso['titulo_curso']}** en {curso['proveedor']} (para desarrollar: *{curso['habilidad']}*)")
    
    # --- SECCIÓN "QUIÉNES SOMOS" ---
    st.markdown("---")
    st.markdown("<h3 id='quienes-somos'>Quiénes Somos</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class='about-card'>
        <b>La Historia de Origen de CogniLink: Conectando Talento con Inteligencia (UNRC - Rosario Castellanos)</b><br><br>
        💡 <b>El Desafío del Crecimiento</b><br>
        La Universidad Nacional Rosario Castellanos (UNRC), como institución innovadora y orientada al futuro, rápidamente se posicionó como un centro vital para la formación de profesionales especializados, en particular en áreas como la Ciencia de Datos para Negocios. Sin embargo, con un rápido crecimiento y un enfoque vanguardista, surgió un desafío: la necesidad de un sistema de vinculación laboral que estuviera a la altura de su modelo educativo.<br><br>
        💻 <b>El Nacimiento de la Solución Inteligente</b><br>
        En 2024, en el octavo semestre de la carrera de Ciencia de Datos para Negocios, Daniela Espinosa y Sofía Casas vieron la oportunidad de aplicar sus conocimientos para transformar esta deficiencia en una ventaja competitiva para su universidad y sus compañeros.
    </div>
    """, unsafe_allow_html=True)

    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.egresado = None
        st.rerun()