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
