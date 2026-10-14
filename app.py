import streamlit as st
from PIL import Image
from io import BytesIO
import os

st.set_page_config(
    page_title="Diagnóstico IA | Errores de PC",
    page_icon="🛠️",
    layout="centered",
)

st.markdown("""
<style>
    .block-container {max-width: 900px; padding-top: 2rem; padding-bottom: 3rem;}
    .hero {padding: 1.5rem; border-radius: 18px; background: linear-gradient(135deg,#101827,#1d4ed8); color: white; margin-bottom: 1rem;}
    .hero h1 {color: white; margin-bottom: .4rem;}
    .muted {color: #64748b;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🛠️ Diagnóstico IA</h1>
  <p>Sube una captura de pantalla y recibe una explicación clara del error y posibles soluciones.</p>
</div>
""", unsafe_allow_html=True)

st.info("Versión inicial: analiza errores de Windows, programas, drivers y computadoras. La IA puede equivocarse; verifica los pasos antes de hacer cambios importantes.")

with st.sidebar:
    st.header("Configuración")
    st.write("Esta aplicación usa la API de Gemini. Necesitas una clave API para habilitar el análisis.")
    st.markdown("[Obtener clave en Google AI Studio](https://aistudio.google.com/apikey)")
    st.caption("No compartas tu clave API ni la escribas en una página pública.")

api_key = ""
try:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key = ""

if not api_key:
    api_key = os.getenv("GEMINI_API_KEY", "")

with st.form("diagnostic_form"):
    uploaded = st.file_uploader(
        "Selecciona una imagen del error",
        type=["png", "jpg", "jpeg", "webp"],
        help="Formatos permitidos: PNG, JPG, JPEG o WEBP. Evita imágenes con contraseñas o datos personales."
    )
    context = st.text_area(
        "Información adicional (opcional)",
        placeholder="Ej.: uso Windows 11, el error aparece al abrir un programa, empezó hoy...",
        max_chars=1500
    )
    submitted = st.form_submit_button("🔎 Analizar error con IA", use_container_width=True)

if uploaded:
    try:
        image = Image.open(uploaded)
        st.image(image, caption="Imagen seleccionada", use_container_width=True)
    except Exception:
        st.error("No se pudo abrir la imagen. Prueba con un archivo PNG o JPG.")

if submitted:
    if not uploaded:
        st.warning("Primero selecciona una imagen.")
    elif not api_key:
        st.error("Falta configurar la clave de Gemini. Sigue los pasos de instalación que aparecen en el archivo README incluido con esta aplicación.")
    else:
        try:
            from google import genai
            from google.genai import types

            image = Image.open(uploaded).convert("RGB")
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=90)
            image_bytes = buffer.getvalue()

            prompt = f"""
Eres un técnico de soporte informático prudente y didáctico. Analiza la imagen adjunta.
El objetivo es diagnosticar errores de Windows, programas, controladores y computadoras.
Información del usuario: {context if context.strip() else "No proporcionó información adicional."}

Responde en español, con esta estructura:
## 1. Error detectado
Transcribe el mensaje o código visible. Si no se puede leer, dilo claramente.
## 2. Qué significa
Explica en palabras sencillas, sin afirmar cosas que la imagen no demuestra.
## 3. Causas probables
Enumera las causas y distingue las más probables de las especulativas.
## 4. Solución paso a paso
Da pasos numerados, empezando por los más sencillos y reversibles. Incluye comandos solo si son necesarios y explica dónde ejecutarlos.
## 5. Cómo comprobar si se solucionó
Indica una prueba sencilla.
## 6. Si el problema continúa
Pide los datos concretos que ayudarían a investigar.
## 7. Riesgo y precauciones
Señala si un paso puede borrar datos, cambiar configuraciones, requerir administrador o afectar el equipo. No recomiendes desactivar antivirus/firewall, descargar ejecutables de sitios desconocidos ni borrar archivos del sistema como primera medida.

No inventes el contenido de la imagen. Si la evidencia es insuficiente, indica el nivel de confianza (alto/medio/bajo) y pide una captura más clara o más contexto. No solicites contraseñas, claves de licencia ni información sensible.
"""
            client = genai.Client(api_key=api_key)
            with st.spinner("La IA está leyendo la imagen y preparando el diagnóstico..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                        prompt
                    ],
                )
            st.markdown("---")
            st.subheader("Resultado del diagnóstico")
            st.markdown(response.text or "La IA no devolvió texto. Intenta con otra imagen.")
            st.download_button(
                "⬇️ Descargar diagnóstico (.txt)",
                data=(response.text or "").encode("utf-8"),
                file_name="diagnostico_error.txt",
                mime="text/plain",
            )
        except Exception as exc:
            st.error("No se pudo completar el análisis. Comprueba tu conexión, la clave API y que tengas cuota disponible.")
            st.caption(f"Detalle técnico: {type(exc).__name__}: {exc}")

st.markdown("---")
st.caption("Privacidad: la imagen se envía al proveedor de IA para analizarla. No subas capturas que contengan contraseñas, datos bancarios, documentos personales o información confidencial.")
