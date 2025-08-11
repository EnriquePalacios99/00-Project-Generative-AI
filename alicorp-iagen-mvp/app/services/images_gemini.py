import os
from io import BytesIO
from typing import List, Tuple
from dotenv import load_dotenv

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

load_dotenv()
GCP_PROJECT  = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")  # región soportada por Imagen

# ---- helpers PIL (reusamos tu lógica y la pulimos) ---------------------------------
def _hex_to_rgb(hex_str: str) -> tuple[int,int,int]:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) for i in (0,2,4))

def _safe_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

def _fit_with_shadow(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    img = img.convert("RGBA")
    img.thumbnail((max_w, max_h), Image.LANCZOS)
    shadow = Image.new("RGBA", (img.width+30, img.height+30), (0,0,0,0))
    s = Image.new("RGBA", (img.width, img.height), (0,0,0,120))
    shadow.paste(s, (15,15), s)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.new("RGBA", (shadow.width, shadow.height), (0,0,0,0))
    canvas.alpha_composite(shadow, (0,0))
    canvas.alpha_composite(img, (0,0))
    return canvas

def _draw_text(draw: ImageDraw.ImageDraw, box, text: str, font, fill=(255,255,255)):
    x0,y0,x1,y1 = box
    max_w = x1-x0
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur+" "+w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    line_h = font.size + 6 if hasattr(font, "size") else 22
    y = y0
    for ln in lines:
        draw.text((x0, y), ln, font=font, fill=fill)
        y += line_h

# ---- llamada a Vertex AI Imagen para generar FONDO IA -------------------------------
def _gen_backgrounds_with_imagen(prompt_bg: str, size: Tuple[int,int], n: int) -> List[Image.Image]:
    """
    Genera 'n' fondos con Imagen (Vertex AI). Devuelve PIL Images (RGB).
    """
    from google.cloud import aiplatform
    from vertexai.preview.vision_models import ImageGenerationModel

    aiplatform.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = ImageGenerationModel.from_pretrained("imagegeneration@002")

    width, height = size

    # Ajusta aspect ratio a lo más cercano admitido por el modelo
    ar = width / height
    if abs(ar - (3/4)) < 0.05:
        aspect_ratio = "3:4"     # 1080x1440 aprox (cercano a 1080x1350)
    elif abs(ar - (1200/628)) < 0.05:
        aspect_ratio = "19.1:10" # aprox 1200x628
    else:
        aspect_ratio = "1:1"

    full_prompt = (
        f"{prompt_bg}\n"
        f"Arte promocional limpio y moderno, sin texto. Fondo con espacio negativo "
        f"para colocar un packshot a la derecha. Iluminación suave, sombras sutiles, "
        f"estilo retail consumo masivo Perú."
    )

    # ¡OJO!: no pasamos 'guidance' (tu SDK no lo soporta)
    # Params comunes válidos: prompt, number_of_images, aspect_ratio, negative_prompt,
    # safety_filter_level, language
    result = model.generate_images(
        prompt=full_prompt,
        number_of_images=n,
        aspect_ratio=aspect_ratio,
        safety_filter_level="block_some",
    )

    outs: List[Image.Image] = []
    for img in result.images:
        # En versiones recientes es 'image_bytes'; mantenemos fallback por compatibilidad
        img_bytes = getattr(img, "image_bytes", None) or getattr(img, "_image_bytes", None)
        pil = Image.open(BytesIO(img_bytes)).convert("RGB")
        pil = pil.resize((width, height), Image.LANCZOS)
        outs.append(pil)
    return outs

# ---- función pública: usa IA para fondo y compone packshot + textos -----------------
def generate_promos_with_gemini_background(
    base_bytes: bytes,
    headline: str,
    subheadline: str,
    cta: str,
    n: int = 1,
    canvas_size: Tuple[int,int] = (1080,1350),
    brand_hex: str = "#E30613",
    prompt_bg: str = "Fondo en colores de la marca, estilo retail fresco",
) -> List[np.ndarray]:
    """
    1) Genera el FONDO con Imagen (Vertex AI).
    2) Superpone packshot + textos con PIL.
    Devuelve lista de np.ndarray para Streamlit.
    """
    if not GCP_PROJECT:
        raise RuntimeError("Configura GCP_PROJECT en .env para usar Vertex AI Imagen.")

    # 1) Fondo IA
    ia_backgrounds = _gen_backgrounds_with_imagen(prompt_bg, canvas_size, n)

    # 2) Composición con packshot
    prod = Image.open(BytesIO(base_bytes)).convert("RGBA")
    brand_rgb = _hex_to_rgb(brand_hex)

    outs = []
    for bg in ia_backgrounds:
        bg = bg.convert("RGBA")
        W, H = bg.size

        # packshot
        pack = _fit_with_shadow(prod, int(W*0.58), int(H*0.55))
        bg.alpha_composite(pack, (int(W*0.52), int(H*0.2)))

        draw = ImageDraw.Draw(bg)
        f_head = _safe_font(int(H*0.06))
        f_sub  = _safe_font(int(H*0.035))
        f_cta  = _safe_font(int(H*0.035))

        margin = int(W*0.07)
        text_w = int(W*0.42)
        x0 = margin
        y0 = int(H*0.18)

        # textos en blanco con trazo suave (para contraste)
        _draw_text(draw, (x0, y0, x0+text_w, y0+int(H*0.18)), headline, f_head, fill=(255,255,255))
        y0 += int(H*0.16)
        _draw_text(draw, (x0, y0, x0+text_w, y0+int(H*0.16)), subheadline, f_sub, fill=(255,255,255))
        y0 += int(H*0.14)

        # CTA pill
        btn_w, btn_h = int(text_w*0.75), int(H*0.08)
        btn_x, btn_y = x0, y0
        radius = int(btn_h/2)
        draw.rounded_rectangle([btn_x, btn_y, btn_x+btn_w, btn_y+btn_h],
                               radius=radius, fill=(255,255,255,235))
        tw = draw.textlength(cta, font=f_cta)
        draw.text((btn_x + (btn_w-tw)/2, btn_y + btn_h/2 - (f_cta.size if hasattr(f_cta,'size') else 18)/2),
                  cta, font=f_cta, fill=brand_rgb)

        outs.append(np.array(bg.convert("RGB")))
    return outs
