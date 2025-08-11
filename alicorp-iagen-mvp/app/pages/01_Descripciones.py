import streamlit as st
from services.llm_gemini import generate_product_description_gemini
# resto igual...

st.title("Generación de descripciones (Gemini)")

with st.form("desc_form"):
    nombre = st.text_input("Nombre del producto", "Snack Saludable Quinoa 120 g")
    atributos = st.text_area("Atributos (texto o JSON breve)", "sabor: coco; sin azúcar; alto en fibra")
    canal = st.selectbox("Canal", ["ecommerce", "marketplace", "redes"])
    imgs = st.file_uploader(
        "Imágenes (opcional, .jpg/.jpeg/.png)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    submitted = st.form_submit_button("Generar")

if submitted:
    image_bytes = [f.getvalue() for f in (imgs or [])] or None

    out = generate_product_description_gemini(
        name=nombre,
        attrs_text=atributos,
        channel=canal,
        image_files=image_bytes,
    )

    st.subheader("Descripción corta")
    st.write(out.get("short", ""))

    st.subheader("Descripción larga (SEO)")
    st.write(out.get("long", ""))

    st.subheader("Bullets")
    bullets = out.get("bullets", [])
    if isinstance(bullets, list) and bullets:
        for b in bullets:
            st.markdown(f"- {b}")
    else:
        st.write("(sin bullets)")

    st.subheader("Hashtags")
    tags = out.get("hashtags", [])
    if isinstance(tags, list) and tags:
        st.code(" ".join(tags))
    else:
        st.code("(sin hashtags)")

    with st.expander("Salida completa (raw)"):
        st.code(out.get("raw", ""))
