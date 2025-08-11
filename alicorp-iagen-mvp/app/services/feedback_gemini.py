import os, json
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT  = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "global")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

def _get_client():
    from google import genai
    if GCP_PROJECT:
        return genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
    if GOOGLE_API_KEY:
        return genai.Client(api_key=GOOGLE_API_KEY)
    raise RuntimeError("Configura GCP_PROJECT (Vertex) o GOOGLE_API_KEY (API pública).")

def summarize_reviews_gemini(reviews: List[str]) -> str:
    """Resumen breve (3–5 bullets) con hallazgos clave."""
    from google.genai import types
    client = _get_client()

    prompt = (
        "Eres un analista de CX para consumo masivo en Perú.\n"
        "Te paso una lista de comentarios de clientes (JSON). Devuélveme un resumen breve con:\n"
        "- 3 a 5 bullets de hallazgos clave (positivos/negativos)\n"
        "- 1 recomendación accionable para marketing/comercial\n"
        "Responde en español, conciso.\n\n"
        f"COMENTARIOS_JSON:\n{json.dumps(reviews[:300], ensure_ascii=False)}"
    )

    config = types.GenerateContentConfig(max_output_tokens=512, temperature=0.4, top_p=0.9)
    resp = client.models.generate_content(model=GEMINI_MODEL,
                                          contents=[types.Content(role="user", parts=[types.Part.from_text(prompt)])],
                                          config=config)
    return (resp.text or "").strip()

def score_sentiment_gemini(reviews: List[str]) -> List[Dict]:
    """Clasificación por comentario: {review, sentiment, rationale}."""
    from google.genai import types
    client = _get_client()

    sys = (
        "Clasifica cada review en: positivo, negativo o neutral. "
        "Devuelve SOLO JSON válido: una lista de objetos "
        '{"review":"...", "sentiment":"positivo|negativo|neutral", "rationale":"breve motivo"}'
    )
    prompt = sys + "\nREVIEWS_JSON:\n" + json.dumps(reviews[:200], ensure_ascii=False)

    config = types.GenerateContentConfig(max_output_tokens=2048, temperature=0.2, top_p=0.9)
    resp = client.models.generate_content(model=GEMINI_MODEL,
                                          contents=[types.Content(role="user", parts=[types.Part.from_text(prompt)])],
                                          config=config)
    text = (resp.text or "").strip()

    # parse robusto
    try:
        return json.loads(text)
    except Exception:
        import re
        m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text, flags=re.I)
        if m:
            return json.loads(m.group(1))
        m2 = re.search(r"(\[[\s\S]*\])", text)
        if m2:
            return json.loads(m2.group(1))
        # fallback vacío si no se pudo parsear
        return [{"review": r[:160], "sentiment": "neutral", "rationale": ""} for r in reviews[:50]]
