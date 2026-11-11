"""Copy your store's catalog into the chatbot database.

    python manage.py sync_products          # scrape https://beyondconnect.store
    python manage.py sync_products --demo   # load a few sample products (offline)

Run it again whenever you add or change products (or schedule it with cron every few hours).
"""
import re
import time
from decimal import Decimal
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from chat.models import Product

PRICE_RE = re.compile(r"₦\s*([\d,]+(?:\.\d+)?)")

DEMO = [
    ("Lightweight White Multi-Speed Road Bike", "Bicycle", 120000, "Sleek and lightweight white road bicycle for smooth urban commuting and fitness.", "lightweight-white-multi-speed-road-bike"),
    ("Modern Matte Black Fluted Glass Outdoor Wall Light", "Light Bulb", 45000, "Modern matte black sconce for entryways, patios or interior walls.", "modern-matte-black-fluted-glass-outdoor-wall-light"),
    ("Luxury Gold Crystal Base Table Lamp with Embroidered Pleated Shade", "Light Bulb", 35000, "Elegant table lamp with a textured gold conical base and crystal neck accents.", "luxury-gold-crystal-base-table-lamp-with-embroidered-pleated-shade"),
    ("Nordic Sculptural Layered Fabric Pendant Light", "Light Bulb", 55000, "Warm, architectural modern sculptural pendant light.", "nordic-sculptural-layered-fabric-pendant-light"),
    ("Modern Gold Hand Wall Light with Frosted Glass Globe", "Light Bulb", 42000, "Unique wall sconce with a polished gold-finish hand holding a frosted glass globe.", "modern-gold-hand-wall-light-with-frosted-glass-globe"),
    ("Modern White LED Ring Chandelier with Fluted Glass Shades", "Light Bulb", 85000, "Ceiling fixture with a sleek white LED halo ring and suspended fluted glass shades.", "modern-white-led-ring-chandelier-with-fluted-glass-shades"),
    ("Grand Multi-Tier Luxury Crystal Chandelier", "Light Bulb", 145000, "Statement lighting fixture with multiple tiers of faceted crystal prisms.", "grand-multi-tier-luxury-crystal-chandelier"),
    ("Modern Glossy Red Teardrop Pendant Light", "Light Bulb", 25000, "Stylish retro-modern pendant light with a glossy red exterior.", "modern-glossy-red-teardrop-pendant-light"),
]


class Command(BaseCommand):
    help = "Import products from the BeyondConnect store into the chatbot database."

    def add_arguments(self, parser):
        parser.add_argument("--base", default=settings.STORE_URL)
        parser.add_argument("--max-pages", type=int, default=40)
        parser.add_argument("--demo", action="store_true", help="Load sample products instead of scraping.")

    def handle(self, *args, **opts):
        base = opts["base"].rstrip("/")
        if opts["demo"]:
            for name, cat, price, desc, slug in DEMO:
                Product.objects.update_or_create(
                    slug=slug,
                    defaults=dict(name=name, category=cat, price=Decimal(price), description=desc,
                                  url=f"{base}/product/{slug}/", in_stock=True),
                )
            self.stdout.write(self.style.SUCCESS(f"Loaded {len(DEMO)} demo products."))
            return

        session = requests.Session()
        session.headers["User-Agent"] = "BeyondConnectChatbot/1.0 (catalog sync)"

        urls, seen_pages = [], set()
        for page in range(1, opts["max_pages"] + 1):
            r = session.get(f"{base}/products/", params={"page": page}, timeout=25)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            found = set()
            for a in soup.select('a[href*="/product/"]'):
                u = urljoin(base + "/", a["href"]).split("?")[0].split("#")[0]
                if urlparse(u).path.startswith("/product/"):
                    found.add(u)
            new = found - seen_pages
            if not new:
                break
            seen_pages |= new
            urls.extend(sorted(new))
            time.sleep(0.4)

        self.stdout.write(f"Found {len(urls)} product pages.")
        count = 0
        for u in urls:
            try:
                r = session.get(u, timeout=25)
                r.raise_for_status()
            except requests.RequestException as e:
                self.stderr.write(f"Skipped {u}: {e}")
                continue
            data = self.parse_product(r.text, u)
            if not data:
                continue
            Product.objects.update_or_create(slug=data.pop("slug"), defaults=data)
            count += 1
            time.sleep(0.3)
        self.stdout.write(self.style.SUCCESS(f"Synced {count} products."))

    def parse_product(self, html, url):
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        if not h1:
            return None
        name = h1.get_text(strip=True)

        price = None
        el = soup.select_one('[class*="price"]')
        scope = el.get_text(" ", strip=True) if el else soup.get_text(" ", strip=True)
        prices = [Decimal(p.replace(",", "")) for p in PRICE_RE.findall(scope)]
        if prices:
            price = min(prices[:2])  # when an old and a sale price are shown, use the lower one

        category = "General"
        cat = soup.select_one("main a[href*='/category/']")
        if cat:
            category = cat.get_text(strip=True)

        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        description = (desc_tag.get("content", "") if desc_tag else "").strip()
        img = soup.find("meta", property="og:image")
        image = img.get("content", "") if img else ""

        text = soup.get_text(" ", strip=True).lower()
        in_stock = not ("out of stock" in text or "sold out" in text)

        slug = urlparse(url).path.rstrip("/").split("/")[-1] or slugify(name)
        return dict(slug=slug[:255], name=name[:255], category=category[:120], price=price,
                    description=description, url=url, image_url=image, in_stock=in_stock)
