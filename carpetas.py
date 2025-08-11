import os, json, textwrap

# === Nombre del proyecto ===
base = "alicorp-iagen-mvp"

def write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Archivos raíz ---
write(f"{base}/.gitignore", textwrap.dedent("""\
__pycache__/
*.pyc
.venv/
.env
.streamlit/
.ipynb_checkpoints/
.DS_Store
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
models/*
!models/.gitkeep
"""))

write(f"{base}/README.md", "# MVP IAGen – Alicorp (Snacks saludables)\n")
write(f"{base}/requirements.txt", "streamlit\npandas\nnumpy\nopenai\nscikit-learn\nmatplotlib\npython-dotenv\n")
write(f"{base}/Dockerfile", textwrap.dedent("""\
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""))

# --- App principal ---
write(f"{base}/app/app.py", textwrap.dedent("""\
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Alicorp IAGen MVP", layout="wide")
st.title("Alicorp – MVP IAGen (Snacks saludables)")
st.markdown("**Usa el menú de la izquierda para navegar.**")
"""))

# --- Páginas ---
write(f"{base}/app/pages/01_Descripciones.py", textwrap.dedent("""\
import streamlit as st
from app.services.llm import generate_product_copies

st.title("Generación de descripciones")
nombre = st.text_input("Producto", "Snack Quinoa 120 g")
atributos = st.text_area("Atributos", "sabor:coco; sin azúcar")
canal = st.selectbox("Canal", ["ecommerce", "marketplace", "redes"])
if st.button("Generar"):
    out = generate_product_copies(nombre, atributos, canal)
    st.write(out)
"""))

write(f"{base}/app/pages/02_Imagenes.py", textwrap.dedent("""\
import streamlit as st
from app.services.images import generate_promo_image

st.title("Imágenes promocionales")
prompt = st.text_area("Prompt", "Packshot snack saludable")
n = st.number_input("N° imágenes", 1, 6, 2)
if st.button("Generar"):
    for img in generate_promo_image(prompt, {"num_images": int(n)}):
        st.image(img)
"""))

write(f"{base}/app/pages/03_Feedback.py", textwrap.dedent("""\
import streamlit as st, pandas as pd
from app.services.feedback import summarize_reviews, score_sentiment

st.title("Feedback de clientes")
up = st.file_uploader("CSV con columnas: review, rating", type=["csv"])
if up:
    df = pd.read_csv(up)
    st.dataframe(df.head())
    st.write("Resumen:", summarize_reviews(df["review"].tolist()))
    st.dataframe(score_sentiment(df["review"].tolist()))
"""))

# --- Servicios ---
write(f"{base}/app/services/__init__.py", "")
write(f"{base}/app/services/utils.py", textwrap.dedent("""\
def parse_attrs(text:str)->dict:
    out={}
    for part in text.split(";"):
        if ":" in part:
            k,v=part.split(":",1)
            out[k.strip()] = v.strip()
    return out
"""))
write(f"{base}/app/services/llm.py", textwrap.dedent("""\
from typing import Dict
from .utils import parse_attrs

def generate_product_copies(name:str, attrs_text:str, channel:str)->Dict:
    attrs = parse_attrs(attrs_text)
    bullets = [f"{k}: {v}" for k,v in attrs.items()]
    return {
        "short": f"{name} ideal para {channel}.",
        "long": f"{name} con atributos {attrs}.",
        "bullets": bullets,
        "hashtags": ["#Alicorp", "#IAgenerativa"]
    }
"""))
write(f"{base}/app/services/images.py", textwrap.dedent("""\
from typing import List
import numpy as np

def generate_promo_image(prompt:str, cfg:dict)->List:
    return [(np.random.rand(256,256,3)*255).astype("uint8") for _ in range(cfg.get("num_images",1))]
"""))
write(f"{base}/app/services/feedback.py", textwrap.dedent("""\
from typing import List, Dict

def summarize_reviews(reviews: List[str]) -> str:
    return f"{len(reviews)} comentarios analizados."

def score_sentiment(reviews: List[str]) -> List[Dict]:
    out=[]
    for r in reviews:
        lab="positivo" if "bueno" in r.lower() else "neutral"
        out.append({"review": r[:50], "sentiment": lab})
    return out
"""))

# --- Config ---
write(f"{base}/config/settings.yaml", "app:\n  name: Alicorp IAGen MVP\n")
write(f"{base}/config/prompt_library.md", "# Prompt templates\n")

# --- Docs ---
write(f"{base}/docs/presentacion/6_slides_outline.md", "1. Problema\n2. Solución\n...")
write(f"{base}/docs/arquitectura/README.md", "Diagramas de arquitectura\n")

# --- Datos ---
write(f"{base}/data/raw/.gitkeep", "")
write(f"{base}/data/processed/.gitkeep", "")
write(f"{base}/data/examples/sample.csv", "name,attrs,channel\nSnack,coco:ecommerce\n")

# --- Models y notebooks ---
write(f"{base}/models/.gitkeep", "")
nb_skel = {"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}
write(f"{base}/notebooks/00_exploracion.ipynb", json.dumps(nb_skel))

# --- Scripts ---
write(f"{base}/scripts/run_local.sh", "#!/usr/bin/env bash\nstreamlit run app/app.py\n")
os.chmod(f"{base}/scripts/run_local.sh", 0o755)

# --- Tests ---
write(f"{base}/tests/test_smoke.py", textwrap.dedent("""\
from app.services.llm import generate_product_copies

def test_smoke():
    out = generate_product_copies("Snack","sabor:coco","ecommerce")
    assert set(out) == {"short","long","bullets","hashtags"}
"""))

# --- CI ---
write(f"{base}/.github/workflows/ci.yml", textwrap.dedent("""\
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.11' }
    - run: pip install -r requirements.txt black isort pytest
    - run: black --check app tests
    - run: isort --check-only app tests
    - run: pytest -q
"""))

print(f"Estructura creada en: {os.path.abspath(base)}")
