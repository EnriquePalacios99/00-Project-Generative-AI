import streamlit as st
import pandas as pd

# Fallback local por si falla Gemini
from services.feedback import summarize_reviews as summarize_local, score_sentiment as score_local

st.title("Feedback de clientes (Gemini)")

def _try_read_csv(file):
    df = pd.read_csv(file, sep=None, engine="python")
    if df.shape[1] == 1 and ";" in df.columns[0]:
        file.seek(0)
        df = pd.read_csv(file, sep=";")
    df.columns = [c.strip().lower() for c in df.columns]
    return df

up = st.file_uploader("CSV con columna de texto (y opcional rating)", type=["csv"])

if up:
    try:
        df = _try_read_csv(up)
    except Exception as e:
        st.error("No se pudo leer el CSV. Verifica separador/encoding.")
        st.exception(e)
        st.stop()

    st.caption("Vista previa")
    st.dataframe(df.head())

    # Detección/selección de columna de texto
    candidates = [c for c in df.columns if c in ["review","comentario","texto","opinion","comment"]]
    text_col = st.selectbox(
        "Selecciona la columna con el texto",
        options=df.columns.tolist(),
        index=(df.columns.get_loc(candidates[0]) if candidates else 0)
    )
    reviews = df[text_col].dropna().astype(str).tolist()
    if not reviews:
        st.warning("No hay textos en la columna seleccionada.")
        st.stop()

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Generar resumen con Gemini"):
            try:
                from services.feedback_gemini import summarize_reviews_gemini
                res = summarize_reviews_gemini(reviews)
                st.subheader("Resumen (Gemini)")
                st.write(res)
            except Exception as e:
                st.warning("Fallo Gemini. Mostrando resumen local.")
                st.write(summarize_local(reviews))
                st.exception(e)

    with c2:
        if st.button("Analizar sentimiento con Gemini"):
            try:
                from services.feedback_gemini import score_sentiment_gemini
                rows = score_sentiment_gemini(reviews)
                st.subheader("Sentimiento por review (Gemini)")
                st.dataframe(pd.DataFrame(rows))
            except Exception as e:
                st.warning("Fallo Gemini. Mostrando análisis local.")
                st.dataframe(pd.DataFrame(score_local(reviews)))
                st.exception(e)
