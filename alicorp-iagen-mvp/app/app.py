import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Alicorp IAGen MVP", layout="wide")
st.title("Alicorp – MVP IAGen (Snacks saludables)")

st.markdown(
    """
**Módulos**
1. *Pages → 01_Descripciones* (Gemini)
2. (Opcional) 02_Imagenes
3. (Opcional) 03_Feedback
"""
)

st.info("Configura tus credenciales en el archivo `.env` en la raíz del proyecto.")
