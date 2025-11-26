from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple
from textwrap import dedent
import streamlit as st # type: ignore


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
# 🧠 EJEMPLO STREAMLIT
# ===============================

if __name__ == "__main__":
    from db_utils import cargar_tabla
    df_egresados = cargar_tabla('egresados')
    df_ofertas = cargar_tabla('ofertas')
    df_habilidades = cargar_tabla('habilidades')

    st.set_page_config(page_title="CogniLink UNRC", layout="wide")

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
    .stFormSubmitButton>button {
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
    .stFormSubmitButton>button:hover {
        background: #0a1f2e;
        color: #00e6e6;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='main-card'>
        <img src='https://files.oaiusercontent.com/file-7b2b6e2e-7e2e-4e2e-8e2e-7e2e7e2e7e2e/imagen.png'>
        <h1>CogniLink UNRC</h1>
        <p style='font-size:1.2rem;'>Sistema inteligente de vinculación laboral para egresados UNRC.<br>Ingresa tu <b>ID de egresado</b> y tu contraseña para ver tu perfil profesional y ofertas relacionadas.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        id_input = st.text_input("ID de egresado", max_chars=10)
        password_input = st.text_input("Ingresa tu contraseña", type="password")
        login_btn = st.form_submit_button("Ingresar")

    if login_btn:
        import pandas as pd
        egresado = df_egresados[df_egresados['ID_Egresado'].astype(str) == id_input]
        # Usar contraseña como nombre para validación (puedes cambiar la lógica si tienes campo de contraseña real)
        if not egresado.empty and egresado.iloc[0]['Nombre'].strip().lower() == password_input.strip().lower():
            st.success(f"Bienvenido/a, {egresado.iloc[0]['Nombre']}!")
            st.markdown("""
            <div style='background: #fff; border-radius: 16px; box-shadow: 0 4px 24px #0a1f2e22; padding: 2rem; margin-top: 2rem; max-width: 700px; margin-left:auto; margin-right:auto;'>
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

            st.markdown("<b>Hard Skills:</b>", unsafe_allow_html=True)
            hard_skills = [h.strip() for h in egresado.iloc[0]['Hard_Skills'].split(',')]
            st.markdown(' '.join([f"<span style='background:#00e6e6; color:#0a1f2e; border-radius:6px; padding:0.3rem 0.8rem; margin:0.2rem; display:inline-block; font-weight:500;'>{skill}</span>" for skill in hard_skills]), unsafe_allow_html=True)

            st.markdown("<b>Soft Skills:</b>", unsafe_allow_html=True)
            soft_skills = [s.strip() for s in egresado.iloc[0]['Soft_Skills'].split(',')]
            st.markdown(' '.join([f"<span style='background:#e6f7ff; color:#0a1f2e; border-radius:6px; padding:0.3rem 0.8rem; margin:0.2rem; display:inline-block; font-weight:500;'>{skill}</span>" for skill in soft_skills]), unsafe_allow_html=True)

            st.markdown(f"<b>Resumen CV:</b> {egresado.iloc[0]['Resumen_CV']}", unsafe_allow_html=True)

            # --- Matching Inteligente de Vacantes y Cursos ---
            st.markdown("<hr><h4 style='color:#00e6e6;'>Matching Inteligente de Vacantes y Cursos</h4>", unsafe_allow_html=True)
            st.info("Pega el texto de tu CV para recibir recomendaciones personalizadas de vacantes y cursos.")
            import re
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            # Cargar datos desde la base de datos
            from db_utils import cargar_tabla
            df_vacantes = cargar_tabla('ofertas')
            df_cursos = pd.DataFrame([
                {"habilidad": "Python", "titulo_curso": "Curso intensivo de Python para Data Science", "proveedor": "Coursera"},
                {"habilidad": "SQL", "titulo_curso": "Introducción a Bases de Datos Relacionales (SQL)", "proveedor": "edX"},
                {"habilidad": "Trabajo en equipo", "titulo_curso": "Taller de Liderazgo y Colaboración Efectiva", "proveedor": "LinkedIn Learning"},
                {"habilidad": "Creatividad", "titulo_curso": "Desarrollo del Pensamiento Creativo Aplicado", "proveedor": "Platzi"}
            ])

            # Convertir DataFrame de vacantes a lista de dicts con claves esperadas
            VACANTES = []
            for _, row in df_vacantes.iterrows():
                VACANTES.append({
                    "id": row["ID_Oferta"],
                    "titulo": row["Puesto"],
                    "empresa": row["Empresa"],
                    "descripcion": row["Descripcion_Puesto"],
                    "requisitos_tecnicos": [h.strip() for h in row["Req_Hard_Skills"].split(",")],
                    "requisitos_blandos": [h.strip() for h in row["Req_Soft_Skills"].split(",")]
                })
            CURSOS = df_cursos.to_dict(orient="records")

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

            # Cursos recomendados según habilidades
            cursos = [
                {"habilidad": "Python", "titulo_curso": "Curso intensivo de Python para Data Science", "proveedor": "Coursera"},
                {"habilidad": "SQL", "titulo_curso": "Introducción a Bases de Datos Relacionales (SQL)", "proveedor": "edX"},
                {"habilidad": "Trabajo en equipo", "titulo_curso": "Taller de Liderazgo y Colaboración Efectiva", "proveedor": "LinkedIn Learning"},
                {"habilidad": "Creatividad", "titulo_curso": "Desarrollo del Pensamiento Creativo Aplicado", "proveedor": "Platzi"}
            ]
            habilidades_usuario = hard_skills + soft_skills
            cursos_rel = [c for c in cursos if c["habilidad"].lower() in [h.lower() for h in habilidades_usuario]]
            st.markdown("<hr><h4 style='color:#00e6e6;'>Cursos Recomendados</h4>", unsafe_allow_html=True)
            if cursos_rel:
                for curso in cursos_rel:
                    st.markdown(f"""
                    <div style='background:#fffbe6; border-radius:12px; padding:1rem; margin-bottom:1rem; max-width:600px; margin-left:auto; margin-right:auto; border-left: 6px solid #00e6e6;'>
                        <b>Habilidad:</b> {curso['habilidad']}<br>
                        <b>Curso:</b> {curso['titulo_curso']}<br>
                        <b>Proveedor:</b> {curso['proveedor']}<br>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay cursos recomendados para tus habilidades actuales.")

            st.markdown("<hr><h4 style='color:#00e6e6;'>Ofertas Relacionadas</h4>", unsafe_allow_html=True)
            ofertas_rel = df_ofertas[df_ofertas['Puesto'].str.contains(egresado.iloc[0]['Rol_Deseado'].split()[0], case=False) | df_ofertas['Req_Hard_Skills'].str.contains(hard_skills[0], case=False)]
            if not ofertas_rel.empty:
                for _, oferta in ofertas_rel.iterrows():
                    st.markdown(f"""
                    <div style='background:#e6f7ff; border-radius:12px; padding:1rem; margin-bottom:1rem; max-width:600px; margin-left:auto; margin-right:auto;'>
                        <b>Puesto:</b> {oferta['Puesto']}<br>
                        <b>Empresa:</b> {oferta['Empresa']}<br>
                        <b>Min. Experiencia (años):</b> {oferta['Min_Exp_Anios']}<br>
                        <b>Hard Skills requeridas:</b> {oferta['Req_Hard_Skills']}<br>
                        <b>Soft Skills requeridas:</b> {oferta['Req_Soft_Skills']}<br>
                        <b>Descripción:</b> {oferta['Descripcion_Puesto']}<br>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay ofertas relacionadas actualmente.")
        else:
            st.error("ID o nombre incorrecto. Por favor, verifica tus datos.")

    # Configuración de Streamlit
    st.set_page_config(page_title="CogniLink UNRC", layout="wide")


    # Colores y logo CogniLink UNRC
    st.markdown("""
    <style>
    body { background-color: #f5faff; }
    .topbar { background: linear-gradient(90deg, #0a1f2e 60%, #00e6e6 100%); color: #fff; padding: 1rem 2rem; display: flex; align-items: center; justify-content: space-between; }
    .logo { font-size: 2rem; font-weight: bold; color: #00e6e6; display: flex; align-items: center; }
    .logo img { height: 48px; margin-right: 12px; vertical-align: middle; }
    .nav button { margin-left: 1rem; background: #fff; color: #0a1f2e; border-radius: 8px; border: none; padding: 0.5rem 1.2rem; font-weight: 600; cursor: pointer; }
    .nav .btn-primary { background: #00e6e6; color: #0a1f2e; }
    .nav .btn-outline { border: 2px solid #00e6e6; background: #fff; color: #00e6e6; }
    .nav .btn-ghost { background: transparent; color: #fff; }
    .card { background: #fff; border-radius: 16px; box-shadow: 0 4px 24px #0a1f2e22; padding: 2rem; margin-top: 2rem; }
    .header h1 { color: #0a1f2e; }
    .habilidades-container span { background: #00e6e6; color: #0a1f2e; border-radius: 6px; padding: 0.3rem 0.8rem; margin: 0.2rem; display: inline-block; font-weight: 500; }
    .plan-card { background: #e6f7ff; border-radius: 12px; padding: 1.2rem; box-shadow: 0 2px 8px #00e6e633; margin-bottom: 1rem; }
    .plan-card h3 { color: #0a1f2e; }
    .plan-card .price { color: #00e6e6; font-size: 1.5rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    # Barra superior
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image("https://files.oaiusercontent.com/file-7b2b6e2e-7e2e-4e2e-8e2e-7e2e7e2e7e2e/imagen.png", width=80)
    with col_title:
        st.markdown("<h1 style='color:#00e6e6; margin-bottom:0;'>CogniLink UNRC</h1>", unsafe_allow_html=True)


    # Estilos para los botones Streamlit
    st.markdown("""
    <style>
    .stButton > button {
        background: #00e6e6;
        color: #0a1f2e;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        margin: 0.5rem 0.5rem 0.5rem 0;
        box-shadow: 0 2px 8px #00e6e633;
        transition: background 0.2s, color 0.2s;
    }
    .stButton > button:hover {
        background: #0a1f2e;
        color: #00e6e6;
    }
    </style>
    """, unsafe_allow_html=True)

    # Quiénes Somos en la parte superior
    st.markdown("<h2 id='quienes-somos' style='color:#0a1f2e; margin-top:2rem;'>Quiénes Somos</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#e6f7ff; border-radius:12px; padding:1.5rem; color:#0a1f2e; font-size:1.1rem;'>
    La Universidad Nacional Rosario Castellanos (UNRC), como institución innovadora y 
    orientada al futuro, rápidamente se posicionó como un centro vital para la formación 
    de profesionales especializados, en particular en áreas como la Ciencia de Datos para 
    Negocios. Sin embargo, con un rápido crecimiento y un enfoque vanguardista, surgió 
    un desafío: la necesidad de un sistema de vinculación laboral que estuviera a la altura 
    de su modelo educativo. <br><br>
    Los métodos tradicionales de networking y ferias de empleo eran insuficientes para un 
    cuerpo estudiantil y de egresados que domina la analítica avanzada. Se requería una 
    solución que hablara el mismo idioma: el lenguaje de los datos. El proceso de 
    matching entre el talento especializado de la UNRC y las vacantes complejas del 
    sector productivo era lento, manual y carecía de la precisión que solo la IA puede 
    ofrecer.<br><br>
    <b>El Nacimiento de la Solución Inteligente</b><br>
    En 2024, en el octavo semestre de la carrera de Ciencia de Datos para Negocios, 
    Daniela Espinosa y Sofía Casas vieron la oportunidad de aplicar sus conocimientos 
    para transformar esta deficiencia en una ventaja competitiva para su universidad y sus 
    compañeros.<br>
    "Nuestro valor como científicos de datos es optimizar la toma de decisiones. ¿Por qué 
    no optimizar la decisión de contratación, usando la inteligencia que ya nos brindan los 
    datos?" — fue la premisa central de su proyecto.<br>
    Utilizando sus habilidades en modelado predictivo, Cómputo Cognitivo y la 
    infraestructura digital de la UNRC, Daniela y Sofía diseñaron la arquitectura de 
    CogniLink. Su objetivo era ir más allá del currículum: la API analizaría el desempeño 
    académico, las competencias blandas y las trayectorias de los egresados para 
    generar un matching basado en la probabilidad de éxito laboral.<br><br>
    <b>¿Qué es CogniLink?</b><br>
    CogniLink nace de la poderosa fusión de la Inteligencia Artificial con la Vinculación 
    Efectiva:<br>
    1. Cognitivo (Cogni): Representa el motor de Inteligencia Artificial que analiza, 
    aprende y realiza un matching predictivo profundo.<br>
    2. Link: Simboliza la Conexión Directa y Automatizada entre el talento de la UNRC y las 
    oportunidades de los sectores público y privado.<br>
    CogniLink se convierte en la herramienta oficial de la UNRC para asegurar que el 
    talento formado bajo sus innovadores modelos educativos se posicione 
    estratégicamente en el mercado. Es la conexión inteligente que garantiza una 
    rentabilidad continua (medida en empleabilidad y posicionamiento) para la 
    universidad, el egresado y las empresas que requieren análisis de datos de alto nivel.
    </div>
    """, unsafe_allow_html=True)


