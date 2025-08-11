import os
import re
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Preferencia por Vertex si hay proyecto configurado
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "global")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")


# ----------------------------- helpers ---------------------------------
def _get_client_and_mode():
    """
    Devuelve (client, mode) donde mode ∈ {"vertex", "public"}.
    Prioriza Vertex si hay GCP_PROJECT configurado, pero:
    - Si FORCE_GEMINI_PUBLIC=true => usa API pública sí o sí.
    - Si Vertex falla por credenciales/permiso => fallback a API pública si hay GOOGLE_API_KEY.
    """
    from google import genai
    import os

    FORCE_PUBLIC = os.getenv("FORCE_GEMINI_PUBLIC", "").lower() in ("1", "true", "yes")

    # 1) Forzar pública si el flag está activo
    if FORCE_PUBLIC and GOOGLE_API_KEY:
        return genai.Client(api_key=GOOGLE_API_KEY), "public"

    # 2) Intentar Vertex si hay proyecto configurado
    if GCP_PROJECT:
        try:
            client = genai.Client(
                vertexai=True,
                project=GCP_PROJECT,
                location=GCP_LOCATION,
            )
            # Verificación temprana: fuerza carga/validación de credenciales
            _ = client.models.list()
            return client, "vertex"
        except Exception:
            # 3) Fallback a pública si hay API key
            if GOOGLE_API_KEY:
                return genai.Client(api_key=GOOGLE_API_KEY), "public"
            # Sin API key disponible: propaga error con mensaje claro
            raise RuntimeError(
                "No se pudo autenticar con Vertex (revisa GOOGLE_APPLICATION_CREDENTIALS, roles IAM, billing). "
                "Además, no hay GOOGLE_API_KEY para fallback a API pública."
            )

    # 4) Sin GCP_PROJECT, usar API pública si hay key
    if GOOGLE_API_KEY:
        return genai.Client(api_key=GOOGLE_API_KEY), "public"

    # 5) Nada configurado
    raise RuntimeError(
        "No se encontró configuración válida. "
        "Configura GCP_PROJECT + credenciales (Vertex) o GOOGLE_API_KEY (API pública), "
        "o usa FORCE_GEMINI_PUBLIC=true para forzar pública."
    )



def _build_contents(name: str, attrs_text: str, channel: str, images: Optional[List[bytes]]):
    """
    Construye el payload (contents) para Gemini: prompt + imágenes opcionales.
    """
    from google.genai import types

    system_prompt = f"""
Eres un redactor experto en e-commerce para consumo masivo en Perú (Alicorp).
Producto: {name}
Atributos: {attrs_text}
Canal: {channel}

DEVUELVE EXCLUSIVAMENTE UN JSON VÁLIDO (sin bloques de código, sin ```).
Estructura exacta:
{{
  "short": "<string 80-120 chars>",
  "long": "<string 90-120 palabras>",
  "bullets": ["<b1>", "<b2>", "<b3>", "<b4>", "<b5>"],
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5", "#tag6"]
}}
Restricciones:
- No incluyas precios.
- Tono cercano, claro, orientado a beneficios; evita claims de salud no verificados.
- Español (Perú), lenguaje sencillo y profesional.
- No inventes sabores/variantes si no están en los atributos; si faltan datos, manténlo genérico.
""".strip()

    parts = [types.Part.from_text(text=system_prompt)]
    if images:
        for b in images:
            # Si tus archivos no son JPEG, cambia mime según corresponda
            parts.append(types.Part.from_bytes(data=b, mime_type="image/jpeg"))

    return [types.Content(role="user", parts=parts)]


def _extract_json(text: str) -> dict:
    """
    Intenta obtener un JSON válido desde la respuesta del modelo aunque venga:
    - dentro de fences ```json ... ```
    - con texto extra antes/después
    """
    # 1) directo
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) fence con ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return json.loads(m.group(1))

    # 3) primer objeto { ... } en el texto
    m2 = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if m2:
        return json.loads(m2.group(1))

    raise ValueError("No se pudo extraer JSON")


def _normalize(out: dict) -> dict:
    """Asegura claves y tipos esperados por la UI."""
    out.setdefault("short", "")
    out.setdefault("long", "")
    out.setdefault("bullets", [])
    out.setdefault("hashtags", [])

    # Si bullets/hashtags llegan como string, convertir a lista
    if isinstance(out["bullets"], str):
        parts = re.split(r"\n|•|-|;", out["bullets"])
        out["bullets"] = [p.strip() for p in parts if p.strip()]

    if isinstance(out["hashtags"], str):
        tags = [t.strip() for t in re.split(r"[,\s]+", out["hashtags"]) if t.strip().startswith("#")]
        out["hashtags"] = tags

    # asegurar lista de strings
    out["bullets"] = [str(x).strip() for x in out["bullets"] if str(x).strip()]
    out["hashtags"] = [str(x).strip() for x in out["hashtags"] if str(x).strip()]
    return out


# ------------------------------ entrypoint ------------------------------
def generate_product_description_gemini(
    name: str,
    attrs_text: str,
    channel: str,
    image_files: Optional[List[bytes]] = None,
    temperature: float = 0.9,
    top_p: float = 0.95,
    max_tokens: int = 1024,
) -> Dict:
    """
    Genera {short, long, bullets, hashtags} con Gemini (Vertex o API pública).
    Tolera respuestas con fences ```json y normaliza la salida para la UI.
    """
    from google.genai import types

    client, _mode = _get_client_and_mode()
    contents = _build_contents(name, attrs_text, channel, image_files)

    config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_tokens,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        ],
        # Si tu SDK soporta esto, descoméntalo para forzar JSON:
        # response_mime_type="application/json",
    )

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=config,
    )

    text = (resp.text or "").strip()

    try:
        parsed = _extract_json(text)
        out = _normalize(parsed)
        out["raw"] = text
        return out
    except Exception:
        # si no se pudo parsear: mostrar raw en la UI para depurar
        return {"short": "", "long": "", "bullets": [], "hashtags": [], "raw": text}
