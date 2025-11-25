from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple
import streamlit as st
import pandas as pd
from db_utils import cargar_tabla

# ===============================
# 📌 CONFIGURACIÓN DE LA PÁGINA
# ===============================
st.set_page_config(page_title="CogniLink UNRC", layout="wide")

# ===============================
# 📌 ESTILOS CSS
# ===============================
def cargar_estilos():
    """Carga los estilos CSS en la aplicación Streamlit."""
    st.markdown("""
    <style>
    /* Estilos generales */
    body {
        background-color: #f0f2f5;
        font-family: 'Lato', sans-serif;
    }

    /* Estilos para la página de login */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        width: 100%;
    }
    .login-card {
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        padding: 3rem;
        width: 100%;
        max-width: 450px;
        text-align: center;
    }
    .login-card img {
        height: 80px;
        margin-bottom: 1.5rem;
    }
    .login-card h1 {
        color: #0a1f2e;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .login-card p {
        color: #555;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Estilos para los widgets de Streamlit */
    .stTextInput>div>input {
        border-radius: 10px;
        border: 1px solid #ddd;
        padding: 1rem;
        font-size: 1rem;
    }
    .stFormSubmitButton>button {
        background: linear-gradient(90deg, #0a1f2e, #007bff);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.8rem 2rem;
        font-weight: 700;
        font-size: 1rem;
        width: 100%;
        margin-top: 1rem;
        transition: all 0.3s ease;
    }
    .stFormSubmitButton>button:hover {
        opacity: 0.9;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.4);
    }

    /* Estilos de la app principal */
    .main-header {
        background: linear-gradient(90deg, #0a1f2e 60%, #00e6e6 100%);
        color: #fff;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
    }
    .main-header img {
        height: 60px;
        margin-right: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ===============================
# 📌 LÓGICA DE AUTENTICACIÓN
# ===============================

def verificar_credenciales(df_egresados: pd.DataFrame, user_id: str, password: str) -> Optional[pd.Series]:
    """Verifica si el ID y la contraseña del egresado son correctos."""
    if not user_id or not password:
        return None
    
    # Busca el egresado por ID
    egresado = df_egresados[df_egresados['ID_Egresado'].astype(str) == user_id]
    
    # Validación (lógica de contraseña debe ser reemplazada por una segura en producción)
    if not egresado.empty and egresado.iloc[0]['Nombre'].strip().lower() == password.strip().lower():
        return egresado.iloc[0]
        
    return None

# ===============================
# 📌 PÁGINA DE INICIO DE SESIÓN
# ===============================

def mostrar_pagina_login(df_egresados: pd.DataFrame):
    """Muestra el formulario de inicio de sesión."""
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    with st.container():
        st.markdown(
            """
            <div class='login-card'>
                <img src='https://files.oaiusercontent.com/file-7b2b6e2e-7e2e-4e2e-8e2e-7e2e7e2e7e2e/imagen.png' alt='Logo CogniLink'>
                <h1>Bienvenido a CogniLink</h1>
                <p>Tu portal profesional en la UNRC. Conectando talento con oportunidades.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            id_input = st.text_input("ID de Egresado", placeholder="Ingresa tu ID", key="login_id")
            password_input = st.text_input("Contraseña", placeholder="Ingresa tu contraseña", type="password", key="login_password")
            login_btn = st.form_submit_button("Ingresar")

            if login_btn:
                egresado_data = verificar_credenciales(df_egresados, id_input, password_input)
                if egresado_data is not None:
                    st.session_state['logged_in'] = True
                    st.session_state['egresado_data'] = egresado_data
                    st.rerun()
                else:
                    st.error("ID de Egresado o Contraseña incorrectos. Por favor, verifica tus datos.")
    st.markdown("</div>", unsafe_allow_html=True)


# ===============================
# 📌 APLICACIÓN PRINCIPAL
# ===============================

def mostrar_app_principal(egresado_data: pd.Series):
    """Muestra el contenido principal de la aplicación tras un login exitoso."""
    
    # Encabezado principal
    st.markdown(f"""
    <div class='main-header'>
        <img src='https://files.oaiusercontent.com/file-7b2b6e2e-7e2e-4e2e-8e2e-7e2e7e2e7e2e/imagen.png' alt='Logo CogniLink'>
        <div>
            <h1 style='color:#00e6e6; margin:0; font-size: 2.5rem;'>CogniLink UNRC</h1>
            <p style='margin:0; font-size: 1.2rem;'>Bienvenido/a, <b>{egresado_data['Nombre']}</b></p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Resto del contenido de la aplicación...
    # (Aquí se pega el código que se mostraba después del login en el archivo original)
    st.markdown("""
    <div style='background: #fff; border-radius: 16px; box-shadow: 0 4px 24px #0a1f2e22; padding: 2rem; margin-top: 2rem; max-width: 700px; margin-left:auto; margin-right:auto;'>
        <div style='display: flex; align-items: center;'>
            <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='48' style='margin-right: 16px;'>
            <h3 style='color:#00e6e6; margin-bottom:0;'>Perfil del Egresado</h3>
        </div>
        <hr>
        <b>ID:</b> {id_input}<br>
        <b>Nombre:</b> {nombre}<br>
        <b>Año de Egreso:</b> {anio_egreso}<br>
        <b>Rol Deseado:</b> {rol_deseado}<br>
        <b>Experiencia (años):</b> {experiencia_anios}<br>
    </div>
    """.format(
        id_input=egresado_data['ID_Egresado'],
        nombre=egresado_data['Nombre'],
        anio_egreso=egresado_data['Anio_Egreso'],
        rol_deseado=egresado_data['Rol_Deseado'],
        experiencia_anios=egresado_data['Experiencia_Anios']
    ), unsafe_allow_html=True)
    
    # ... (El resto del código de matching, cursos, etc. iría aquí) ...

    # Sección Quiénes Somos (ahora dentro de la app principal)
    st.markdown("<h2 id='quienes-somos' style='color:#0a1f2e; margin-top:3rem;'>Quiénes Somos</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#e6f7ff; border-radius:12px; padding:1.5rem; color:#0a1f2e; font-size:1.1rem;'>
    La Universidad Nacional Rosario Castellanos (UNRC), como institución innovadora y 
    orientada al futuro, rápidamente se posicionó como un centro vital para la formación 
    de profesionales especializados... (y el resto del texto).
    </div>
    """, unsafe_allow_html=True)

    if st.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.session_state.pop('egresado_data', None)
        st.rerun()

# ===============================
# 📌 PUNTO DE ENTRADA
# ===============================

def main():
    """Función principal que orquesta la aplicación."""
    cargar_estilos()

    # Inicializar estado de sesión
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['egresado_data'] = None

    # Cargar datos una vez
    if 'df_egresados' not in st.session_state:
        st.session_state.df_egresados = cargar_tabla('egresados')
        st.session_state.df_ofertas = cargar_tabla('ofertas')
        st.session_state.df_habilidades = cargar_tabla('habilidades')

    # Enrutamiento: mostrar login o app principal
    if st.session_state['logged_in'] and st.session_state['egresado_data'] is not None:
        mostrar_app_principal(st.session_state['egresado_data'])
    else:
        mostrar_pagina_login(st.session_state.df_egresados)


if __name__ == "__main__":
    main()