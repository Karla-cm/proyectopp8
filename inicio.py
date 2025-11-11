from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple
from textwrap import dedent
import streamlit as st


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
    exp1 = ExperienciaLaboral(
        puesto="Desarrollador Backend Python",
        empresa="Tech Solutions Inc.",
        descripcion="Desarrollo y mantenimiento de APIs REST para la plataforma principal.",
        fecha_inicio=date(2021, 1, 15),
    )

    exp2 = ExperienciaLaboral(
        puesto="Desarrollador Junior",
        empresa="Web Starters LLC",
        descripcion="Maquetación de sitios web y soporte a desarrolladores senior.",
        fecha_inicio=date(2019, 6, 1),
        fecha_fin=date(2020, 12, 31)
    )

    perfil_juan = PerfilCandidato(
        nombre="Juan Pérez",
        email="juan.perez@email.com",
        telefono="555-123-4567",
        resumen_profesional="Ingeniero de software con 5 años de experiencia en desarrollo web, especializado en backend con Python y Django."
    )

    for habilidad in ["Python", "Django", "SQL", "Docker"]:
        perfil_juan.agregar_habilidad(habilidad)

    for exp in [exp1, exp2]:
        perfil_juan.agregar_experiencia(exp)

    oferta_backend = OfertaDeTrabajo(
        puesto="Ingeniero Backend Senior",
        empresa="Innovatech",
        habilidades_requeridas=["Python", "Django", "PostgreSQL", "Docker", "AWS"]
    )

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

    # Interactividad de botones
    st.markdown("<hr>", unsafe_allow_html=True)
    seleccion = st.radio(
        "Selecciona una opción:",
        ("Ingresar", "Suscribirse", "Quiénes Somos"),
        horizontal=True
    )

    if seleccion == "Ingresar":
        st.info("Funcionalidad de ingreso próximamente disponible.")
    elif seleccion == "Suscribirse":
        st.success("¡Gracias por tu interés! La suscripción estará habilitada pronto.")
    elif seleccion == "Quiénes Somos":
        st.markdown("<h2 id='quienes-somos' style='color:#0a1f2e;'>Quiénes Somos</h2>", unsafe_allow_html=True)
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

    if st.button("Ver mi Perfil"):
        st.session_state.mostrar_perfil = not st.session_state.get('mostrar_perfil', False)

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.session_state.get('mostrar_perfil', False):
            st.markdown(perfil_juan.generar_html(), unsafe_allow_html=True)

    with col2:
        if st.session_state.get('mostrar_perfil', False):
            compatibilidad, coincidentes, faltantes = verificar_compatibilidad(perfil_juan, oferta_backend)
            st.subheader(f"Análisis de compatibilidad:")
            st.info(f"**{oferta_backend.puesto}** en **{oferta_backend.empresa}**")
            st.metric("Compatibilidad de Habilidades", f"{compatibilidad}%")
            st.success(f"**Coinciden ({len(coincidentes)}):** {', '.join(coincidentes)}")
            st.warning(f"**Faltan ({len(faltantes)}):** {', '.join(faltantes)}")


