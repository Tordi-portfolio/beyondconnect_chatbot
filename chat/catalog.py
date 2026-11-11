"""Tiny keyword retriever: picks the products most relevant to what the customer is asking."""
import re

from .models import Product

STOP_WORDS = {
    "the", "and", "for", "you", "with", "have", "any", "can", "how", "much", "what", "your",
    "are", "this", "that", "want", "need", "buy", "get", "price", "show", "tell", "about",
    "please", "something", "good", "best", "one", "some", "which", "does", "do", "is", "a",
}

# customer word -> extra words that may appear in product names/categories
SYNONYMS = {
    "ac": ["air", "conditioner", "cooling"],
    "aircon": ["air", "conditioner"],
    "fridge": ["refrigerator", "freezer"],
    "refrigerator": ["fridge", "freezer"],
    "freezer": ["fridge"],
    "bulb": ["light", "lamp", "led"],
    "bulbs": ["light", "lamp", "led"],
    "lamp": ["light", "lighting"],
    "lighting": ["light", "lamp", "chandelier", "pendant"],
    "chandelier": ["light"],
    "washer": ["washing", "machine"],
    "bike": ["bicycle"],
    "cooker": ["gas", "electric", "stove"],
    "stove": ["cooker"],
    "sofa": ["chair", "furniture"],
    "couch": ["chair", "furniture"],
    "seat": ["chair"],
    "desk": ["table"],
}


def tokens(text):
    out = []
    for t in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if t in STOP_WORDS:
            continue
        if len(t) < 2:
            continue
        out.append(t)
        out.extend(SYNONYMS.get(t, []))
    return set(out)


def relevant_products(query, limit=8):
    q = tokens(query)
    scored = []
    for p in Product.objects.all():
        name_t, cat_t, desc_t = tokens(p.name), tokens(p.category), tokens(p.description)
        score = 3 * len(q & name_t) + 2 * len(q & cat_t) + len(q & desc_t)
        if score:
            scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], x[1].name))
    results = [p for _, p in scored[:limit]]
    if not results:  # nothing matched: show a few in-stock items so the bot has something real to offer
        results = list(Product.objects.filter(in_stock=True).order_by("-updated_at")[:6])
    return results


def format_product(p):
    price = f"₦{p.price:,.0f}" if p.price is not None else "price on request"
    stock = "in stock" if p.in_stock else "OUT OF STOCK"
    desc = (p.description or "").strip().replace("\n", " ")[:220]
    return f"- {p.name} | {p.category} | {price} | {stock} | {p.url or ''} | {desc}"


def category_summary():
    from django.db.models import Count

    rows = Product.objects.values("category").annotate(n=Count("id")).order_by("category")
    return ", ".join(f"{r['category']} ({r['n']})" for r in rows) or "no products loaded yet"
