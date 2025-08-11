import streamlit as st

try:
    from services.images_gemini import generate_promos_with_gemini_background
except Exception as e:
    st.error("No se pudo importar services.images_gemini. Revisa el archivo y el __init__.py.")
    st.exception(e)
    st.stop()

st.title("Imágenes promocionales (con GenAI de Google)")

colp = st.columns(2)
with colp[0]:
    base = st.file_uploader("Sube la imagen del producto (packshot)", type=["jpg","jpeg","png"])
with colp[1]:
    formato = st.selectbox("Formato", ["1080x1350 (IG Feed)", "1200x628 (Ads)"])

headline = st.text_input("Titular", "Nuevo Cereales Ángel")
subheadline = st.text_input("Subtítulo", "Más sabor para tus mañanas")
cta = st.text_input("CTA", "Compra ahora")
num = st.number_input("N° imágenes", 1, 4, 1)

prompt_bg = st.text_area(
    "Prompt del fondo (IA)",
    "Fondo con gradientes suaves en colores de la marca, moderno, retail, limpio."
)
brand_color = st.color_picker("Color principal (para CTA)", "#E30613")

if st.button("Generar", type="primary"):
    if not base:
        st.warning("Sube un packshot para continuar.")
        st.stop()

    size = (1080, 1350) if "1080x1350" in formato else (1200, 628)

    try:
        imgs = generate_promos_with_gemini_background(
            base.read(),
            headline=headline,
            subheadline=subheadline,
            cta=cta,
            n=int(num),
            canvas_size=size,
            brand_hex=brand_color,
            prompt_bg=prompt_bg,
        )
        for i, im in enumerate(imgs, 1):
            st.image(im, caption=f"Creatividad {i}")
    except Exception as e:
        st.error("Error generando con Vertex AI Imagen. Revisa credenciales y variables .env.")
        st.exception(e)
