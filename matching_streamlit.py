import streamlit as st
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- CARGAR MOCK DATA ---
try:
    with open('vacantes.json', 'r', encoding='utf-8') as f:
        VACANTES = json.load(f)
    with open('cursos.json', 'r', encoding='utf-8') as f:
        CURSOS = json.load(f)
except FileNotFoundError:
    VACANTES = []
    CURSOS = []

# --- FUNCIONES DE NLP ---
def normalizar_habilidad(habilidad):
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
    habilidades_encontradas = set()
    habilidades_normalizadas = [normalizar_habilidad(h) for h in lista_habilidades_conocidas]
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
    tfidf_scores = {}
    for i, score in enumerate(scores):
        vacante_id = vacantes[i]['id']
        tfidf_scores[vacante_id] = score
    return tfidf_scores

# --- STREAMLIT UI ---
st.set_page_config(page_title="Matching Inteligente de Vacantes y Cursos", layout="wide")
st.title("Matching Inteligente de Vacantes y Cursos")

cv_texto = st.text_area("Pega aquí el texto de tu CV para analizar tu perfil y recomendarte vacantes y cursos:")

if st.button("Analizar y Recomendar"):
    if not cv_texto.strip():
        st.error("Debes ingresar el texto de tu CV.")
    else:
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
        for res in resultados_ordenados:
            v = res["vacante"]
            st.markdown(f"### {v['titulo']} ({v['empresa']})")
            st.markdown(f"**Puntaje de match:** {res['puntaje_match']}%")
            st.markdown(f"**Habilidades cumplidas:** {', '.join(res['habilidades_cumplidas'])}")
            st.markdown(f"**Habilidades faltantes:** {', '.join(res['habilidades_faltantes'])}")
            st.markdown("**Cursos recomendados:**")
            for curso in res["cursos_recomendados"]:
                st.markdown(f"- {curso['titulo_curso']} ({curso['proveedor']}) [{curso['habilidad']}]")
            st.markdown("---")
