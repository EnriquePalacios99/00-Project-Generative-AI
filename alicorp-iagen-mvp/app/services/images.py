from typing import List, Tuple
from io import BytesIO
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def _hex_to_rgb(hex_str: str) -> Tuple[int,int,int]:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) for i in (0,2,4))

def _make_bg(size: Tuple[int,int], style: str, brand_rgb: Tuple[int,int,int]) -> Image.Image:
    w, h = size
    if style == "blanco":
        return Image.new("RGB", size, (255,255,255))
    if style == "sólido":
        return Image.new("RGB", size, brand_rgb)
    # degradado
    bg = Image.new("RGB", size, (255,255,255))
    top = brand_rgb
    bottom = (248,248,248)
    draw = ImageDraw.Draw(bg)
    for y in range(h):
        t = y/(h-1)
        r = int((1-t)*top[0] + t*bottom[0])
        g = int((1-t)*top[1] + t*bottom[1])
        b = int((1-t)*top[2] + t*bottom[2])
        draw.line([(0,y),(w,y)], fill=(r,g,b))
    return bg

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

def _safe_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

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

def generate_creatives_from_base(
    base_bytes: bytes,
    headline: str,
    subheadline: str,
    cta: str,
    n: int = 1,
    canvas_size: Tuple[int,int] = (1080,1350),
    bg_style: str = "degradado",
    brand_hex: str = "#E30613",
) -> List[np.ndarray]:
    brand_rgb = _hex_to_rgb(brand_hex)
    prod = Image.open(BytesIO(base_bytes)).convert("RGBA")

    outs = []
    for _ in range(n):
        bg = _make_bg(canvas_size, bg_style, brand_rgb).convert("RGBA")
        W,H = bg.size

        pack = _fit_with_shadow(prod, int(W*0.65), int(H*0.55))
        bg.alpha_composite(pack, (int(W*0.52), int(H*0.18)))

        draw = ImageDraw.Draw(bg)
        f_head = _safe_font(int(H*0.06))
        f_sub  = _safe_font(int(H*0.035))
        f_cta  = _safe_font(int(H*0.035))

        margin = int(W*0.07)
        text_w = int(W*0.42)
        x0 = margin
        y0 = int(H*0.18)

        _draw_text(draw, (x0, y0, x0+text_w, y0+int(H*0.18)), headline, f_head)
        y0 += int(H*0.16)
        _draw_text(draw, (x0, y0, x0+text_w, y0+int(H*0.16)), subheadline, f_sub)
        y0 += int(H*0.14)

        # CTA pill
        btn_w, btn_h = int(text_w*0.75), int(H*0.08)
        btn_x, btn_y = x0, y0
        radius = int(btn_h/2)
        draw.rounded_rectangle([btn_x, btn_y, btn_x+btn_w, btn_y+btn_h],
                               radius=radius, fill=(255,255,255,230))
        tw = draw.textlength(cta, font=f_cta)
        draw.text((btn_x + (btn_w-tw)/2, btn_y + btn_h/2 - (f_cta.size if hasattr(f_cta,'size') else 18)/2),
                  cta, font=f_cta, fill=brand_rgb)

        outs.append(np.array(bg.convert("RGB")))
    return outs
