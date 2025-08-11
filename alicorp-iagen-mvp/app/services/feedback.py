from typing import List, Dict

POS = {"bueno","excelente","rico","delicioso","me encanta","recomendado","perfecto","genial","sabroso","agradable"}
NEG = {"malo","horrible","feo","asqueroso","no me gusta","pésimo","defecto","tardó","caro"}

def summarize_reviews(reviews: List[str]) -> str:
    return f"{len(reviews)} comentarios analizados."

def score_sentiment(reviews: List[str]) -> List[Dict]:
    out = []
    for r in reviews:
        rl = r.lower()
        score = 0
        score += sum(1 for w in POS if w in rl)
        score -= sum(1 for w in NEG if w in rl)
        lab = "positivo" if score > 0 else ("negativo" if score < 0 else "neutral")
        out.append({"review": r[:120], "sentiment": lab})
    return out
