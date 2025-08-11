from app.services.llm import generate_product_copies

def test_smoke():
    out = generate_product_copies("Snack","sabor:coco","ecommerce")
    assert set(out) == {"short","long","bullets","hashtags"}
