#!/usr/bin/env python3
"""
Nippon Nites – static site generator.

Liest die Produktdaten aus data/products.json (Shopify /products.json Export)
und erzeugt eine komplett statische, SEO-optimierte Website im Repo-Root.

    python3 build.py            # baut die Seite aus data/products.json
    python3 build.py --fetch    # holt vorher frische Produktdaten von nipponnites.com

Die URL-Struktur spiegelt bewusst die bestehende Shopify-Struktur
(/products/<handle>, /collections/all, /pages/<seite>), damit beim Livegang
keine Rankings verloren gehen und alle Canonicals stimmen.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DATA = ROOT / "data" / "products.json"

SITE = "https://nipponnites.com"
SHOP = "https://nipponnites.com"  # Shopify-Checkout
# Vorschau: noindex, damit Google die Kopie nicht als Duplicate Content wertet.
# Beim Livegang auf False setzen.
PREVIEW = True
PROMO = "−20 % auf alle Customs"  # leer lassen, um die Leiste auszublenden

BRAND = {
    "name": "Nippon Nites",
    "email": "info@nipponnites.com",
    "street": "Im Grüntal 10",
    "zip": "8405",
    "city": "Winterthur",
    "region": "ZH",
    "country": "CH",
    "instagram": "https://www.instagram.com/nipponnites/",
    "tiktok": "https://www.tiktok.com/@nippon_nites",
    "founder": "Fabio Berta",
    "founded": "2024",
}

CATS = {
    "T-Shirt": ("tshirts", "T-Shirts"),
    "Hoodie": ("hoodies", "Hoodies"),
    "Cap": ("headwear", "Caps & Beanies"),
    "Beanie": ("headwear", "Caps & Beanies"),
    "Bundle": ("bundles", "Bundles"),
    "Accessoire": ("accessoires", "Accessoires"),
    "Custom": ("custom", "Custom"),
    "Geschenkkarte": ("gutscheine", "Gutscheine"),
}
CAT_ORDER = ["hoodies", "tshirts", "custom", "headwear", "bundles", "accessoires", "gutscheine"]

# Saubere Anzeigenamen, wo der Shopify-Titel irreführend ist
TITLE_FIX = {
    "nippon-nites-beanie-white-1": "Nippon Nites Beanie – Colour",
    "nippon-nites-beanie-white": "Nippon Nites Beanie – Classic",
    "nippon-nites-geschenkgutschein": "Geschenkgutschein",
}

FAQ = [
    ("Bestellung & Versand", [
        ("Wie lange dauert die Lieferung?",
         "Standard-Artikel brauchen ca. 10 Tage – jedes Teil wird erst nach deiner Bestellung für dich produziert. "
         "So vermeiden wir Überproduktion und Lagerware. Custom-Designs: 1–2 Wochen Illustration & Produktion plus ca. 10 Tage Lieferung."),
        ("Liefert ihr auch nach Deutschland, Österreich und weltweit?",
         "Ja. Schweiz & Deutschland: 7–12 Werktage. Österreich & restliches Europa: 10–15 Werktage. "
         "USA & Rest der Welt: 10–20 Werktage. Alle Zeiten inkl. Produktion und Versand."),
        ("Wie verfolge ich meine Bestellung?",
         "Sobald dein Paket unterwegs ist, bekommst du automatisch eine E-Mail mit Tracking-Link. "
         "Fragen? Schreib an info@nipponnites.com."),
        ("Wie kann ich bezahlen?",
         "Mit TWINT, PayPal oder Kreditkarte – sicher über den Shopify-Checkout."),
    ]),
    ("Rückgabe & Umtausch", [
        ("Kann ich zurückgeben oder umtauschen?",
         "Standard-Produkte kannst du innerhalb von 14 Tagen zurückgeben oder umtauschen – ungetragen und mit Etikett. "
         "Custom-Bestellungen sind ausgeschlossen, weil sie nur für dich angefertigt werden."),
        ("Mein Artikel ist falsch oder beschädigt – was jetzt?",
         "Schreib uns sofort an info@nipponnites.com mit Foto und Bestellnummer. Wir kümmern uns umgehend darum."),
    ]),
    ("Custom-Merch", [
        ("Wie funktioniert eine Custom-Bestellung?",
         "1. Du bestellst Custom-Hoodie oder -T-Shirt im Shop. 2. Wir melden uns per E-Mail. "
         "3. Du schickst Fotos deines Autos und deine Ideen. 4. Fabio illustriert dein Unikat von Hand. 5. Produktion und Versand."),
        ("Welche Autos könnt ihr illustrieren?",
         "Jedes. JDM-Klassiker, Euro-Sportwagen, Muscle Cars, Projektautos – wenn du es fährst, zeichnen wir es."),
        ("Kann ich mein eigenes Logo oder eine Skizze einsenden?",
         "Ja. Schick uns Idee, Skizze oder Referenzbilder – wir setzen es gemeinsam mit dir im Nippon-Nites-Stil um."),
        ("Nutzt ihr KI für die Designs?",
         "Nein. Jedes Design – ob Drop oder Custom – wird von Hand illustriert. Das ist uns wichtig."),
    ]),
    ("Material & Passform", [
        ("Wie fallen die Grössen aus?",
         "Shirts und Hoodies sind bewusst im Oversized- bzw. Boxy-Schnitt. Die klassischen Hoodies fallen eher klein aus – "
         "im Zweifel eine Grösse grösser wählen. Die Grössentabelle findest du auf jeder Produktseite."),
        ("Wie pflege ich Shirt und Hoodie?",
         "Auf links gedreht bei max. 30 °C waschen, nicht in den Trockner, Druck- und Stickbereiche nicht bügeln. "
         "So bleibt das Motiv jahrelang scharf."),
        ("Welche Materialien verwendet ihr?",
         "Je nach Modell Bio-Baumwolle oder schwere Heavyweight-Baumwolle bis 280 g/m². Die genaue Zusammensetzung "
         "steht bei jedem Produkt."),
    ]),
]

# ---------------------------------------------------------------- helpers

e = lambda s: html.escape(str(s), quote=True)


def chf(v) -> str:
    return f"CHF {float(v):.2f}"


def cdn(src: str, w: int) -> str:
    sep = "&" if "?" in src else "?"
    return f"{src}{sep}width={w}"


def img(src, alt, sizes, w=1200, h=1200, eager=False, cls="", widths=(360, 540, 720, 1080)):
    srcset = ", ".join(f"{e(cdn(src, x))} {x}w" for x in widths)
    load = 'fetchpriority="high" loading="eager"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="{e(cdn(src, widths[1]))}" srcset="{srcset}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{e(alt)}" decoding="async" {load}>')


def strip_tags(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())


def clean_body(s: str, title: str) -> str:
    s = re.sub(r"(?is)<(script|style|meta|img|iframe)[^>]*>.*?(</\1>)?", "", s or "")
    s = re.sub(r"(?i)</?(span|div|font|meta)[^>]*>", "", s)
    s = re.sub(r'(?i)\s(class|style|data-[\w-]+|id|dir)="[^"]*"', "", s)
    s = re.sub(r"(?i)<(/?)h[12]>", r"<\1h3>", s)
    s = re.sub(r"(?i)<(/?)b>", r"<\1strong>", s)
    s = re.sub(r"(?i)<p>\s*(<br\s*/?>)?\s*</p>", "", s)
    s = re.sub(r"<br>\s*</li>", "</li>", s)
    # Titel, der als Überschrift wiederholt wird, entfernen
    s = re.sub(r"(?is)^\s*<h3>\s*(<strong>)?\s*" + re.escape(title.split("|")[0].strip()[:12]) + r".*?</h3>", "", s)
    return s.strip()


def tz_attr(p) -> str:
    return e(p)


# ---------------------------------------------------------------- data

def load_products():
    raw = json.loads(DATA.read_text())["products"]
    out = []
    for p in raw:
        slug, cat = CATS.get(p["product_type"], ("accessoires", p["product_type"] or "Sonstiges"))
        prices = sorted({float(v["price"]) for v in p["variants"]})
        title = TITLE_FIX.get(p["handle"], p["title"].replace(" | ", " · "))
        images = [{"src": i["src"].replace("http://", "https://"), "w": i.get("width") or 1200,
                   "h": i.get("height") or 1200} for i in p["images"]]
        # Grössentabellen-Bilder ans Ende
        images.sort(key=lambda i: "size-img" in i["src"])
        variants = [{
            "id": v["id"], "title": v["title"], "price": float(v["price"]),
            "compare": float(v["compare_at_price"]) if v.get("compare_at_price") else None,
            "available": v["available"], "options": [v.get("option1"), v.get("option2"), v.get("option3")],
            "img": (v.get("featured_image") or {}).get("src"),
        } for v in p["variants"]]
        options = [{"name": o["name"].replace("Größe", "Grösse").replace("Color", "Farbe").replace("Size", "Grösse")
                    .replace("KONNICHIWA MTHRFCKRS (Grösse)", "Grösse"),
                    "values": o["values"]} for o in p["options"] if o["name"] != "Title"]
        desc = strip_tags(p["body_html"])
        out.append({
            "handle": p["handle"], "title": title, "type": p["product_type"], "cat": cat, "cat_slug": slug,
            "tags": p["tags"], "min": prices[0], "max": prices[-1], "images": images, "variants": variants,
            "options": options, "body": clean_body(p["body_html"], p["title"]), "desc": desc,
            "created": p["created_at"][:10], "updated": p["updated_at"][:10],
            "available": any(v["available"] for v in p["variants"]),
        })
    out.sort(key=lambda x: x["created"], reverse=True)
    return out


# ---------------------------------------------------------------- layout

NAV = [
    ("collections/all/", "Shop"),
    ("pages/custom/", "Custom"),
    ("pages/brandstory/", "Story"),
    ("pages/faq/", "FAQ"),
    ("pages/contact/", "Kontakt"),
]

FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,100..900;1,62..125,400..700"
         "&family=JetBrains+Mono:wght@400;500&display=swap")
JP_TEXT = "日本の夜走首都高速道路ニッポンナイツ手描き夜行"
FONT_JP = f"https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700&display=swap&text={urllib.request.quote(JP_TEXT)}"

MARK_SVG = (SRC / "assets" / "logo-mark.svg").read_text()
MARK_PATH = re.search(r"<path[^>]*/>", MARK_SVG).group(0)
WORD_SVG = (SRC / "assets" / "logo-word.svg").read_text()


def mark(cls="", label=None):
    a = f'role="img" aria-label="{e(label)}"' if label else 'aria-hidden="true"'
    return MARK_SVG.replace("<svg ", f'<svg class="{cls}" {a} ', 1)


def word(cls="", label="Nippon Nites"):
    return WORD_SVG.replace("<svg ", f'<svg class="{cls}" role="img" aria-label="{e(label)}" ', 1)


def ld(obj) -> str:
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False, separators=(",", ":"))}</script>'


ORG = {
    "@type": ["Organization", "OnlineStore"],
    "@id": f"{SITE}/#org",
    "name": BRAND["name"],
    "alternateName": "NIPPON NITES",
    "url": f"{SITE}/",
    "logo": f"{SITE}/assets/icon-512.png",
    "image": f"{SITE}/assets/og.jpg",
    "description": "JDM-Streetwear und Custom-Car-Merch aus Winterthur. Jedes Design von Hand illustriert.",
    "email": BRAND["email"],
    "foundingDate": BRAND["founded"],
    "founder": {"@type": "Person", "name": BRAND["founder"], "url": f"{SITE}/pages/brandstory"},
    "address": {"@type": "PostalAddress", "streetAddress": BRAND["street"], "postalCode": BRAND["zip"],
                "addressLocality": BRAND["city"], "addressRegion": BRAND["region"], "addressCountry": BRAND["country"]},
    "areaServed": ["CH", "DE", "AT", "EU"],
    "sameAs": [BRAND["instagram"], BRAND["tiktok"]],
    "paymentAccepted": "TWINT, PayPal, Kreditkarte",
    "currenciesAccepted": "CHF",
    "hasMerchantReturnPolicy": {
        "@type": "MerchantReturnPolicy", "applicableCountry": "CH",
        "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow", "merchantReturnDays": 14,
        "returnMethod": "https://schema.org/ReturnByMail",
    },
}


def crumbs_ld(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{SITE}{u}"} for i, (n, u) in enumerate(items)]}


def crumbs_html(pre, items):
    li = []
    for i, (n, u, local) in enumerate(items):
        if i == len(items) - 1:
            li.append(f'<li aria-current="page">{e(n)}</li>')
        else:
            li.append(f'<li><a href="{pre}{local}">{e(n)}</a></li>')
    return f'<nav class="crumbs" aria-label="Brotkrumen"><ol>{"".join(li)}</ol></nav>'


def page(*, path, title, desc, body, canonical, schema=(), og_image=None, og_type="website", depth=0,
         body_class="", head_extra="", is_404=False):
    pre = "../" * depth
    # GitHub Pages liefert 404.html unter beliebigen Pfaden aus -> Basis-URL setzen
    base_fix = ("<script>(function(){var p=location.pathname.split('/');var b=location.hostname.endsWith('github.io')&&p[1]?'/'+p[1]+'/':'/';document.write('<base href=\"'+b+'\">')})()</script>\n" if is_404 else "")
    og_image = og_image or f"{SITE}/assets/og.jpg"
    graph = {"@context": "https://schema.org", "@graph": [ORG, {
        "@type": "WebSite", "@id": f"{SITE}/#web", "url": f"{SITE}/", "name": "Nippon Nites", "inLanguage": "de-CH",
        "publisher": {"@id": f"{SITE}/#org"},
        "potentialAction": {"@type": "SearchAction", "target": f"{SITE}/search?q={{q}}", "query-input": "required name=q"},
    }, *schema]}
    nav = "".join(
        f'<li><a href="{pre}{u}"{" aria-current=\"page\"" if path.startswith(u) else ""}>{t}</a></li>' for u, t in NAV)
    promo = (f'<div class="promo"><a href="{pre}pages/custom/"><span class="dot"></span>{e(PROMO)} '
             f'<span class="promo-arrow" aria-hidden="true">→</span></a></div>') if PROMO else ""
    robots = "noindex, follow" if PREVIEW else "index, follow, max-image-preview:large"
    return f"""<!doctype html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
{base_fix}<script>document.documentElement.classList.add('js')</script>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="de-CH" href="{canonical}">
<link rel="alternate" hreflang="de" href="{canonical}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<meta name="theme-color" content="#0a0a0b">
<meta name="color-scheme" content="dark">
<meta property="og:site_name" content="Nippon Nites">
<meta property="og:locale" content="de_CH">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{e(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="geo.region" content="CH-ZH">
<meta name="geo.placename" content="Winterthur">
<link rel="icon" href="{pre}assets/logo-mark.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{pre}assets/apple-touch-icon.png">
<link rel="manifest" href="{pre}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdn.shopify.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{FONT_JP}">
<link rel="stylesheet" href="{pre}assets/style.css">
<script src="{pre}assets/app.js" defer></script>
{head_extra}{ld(graph)}
</head>
<body class="{body_class}" data-root="{pre}" data-shop="{SHOP}">
<a class="skip" href="#main">Zum Inhalt springen</a>
{promo}
<header class="site-header" id="top">
  <div class="wrap header-in">
    <a class="brand" href="{pre if pre else './'}" aria-label="Nippon Nites – Startseite">{mark("brand-mark")}<span class="brand-word">Nippon&nbsp;Nites</span></a>
    <nav class="main-nav" aria-label="Hauptnavigation"><ul>{nav}</ul></nav>
    <div class="header-tools">
      <span class="clock mono" data-clock aria-label="Uhrzeit Winterthur und Tokio">
        <span><abbr title="Winterthur">WTH</abbr> <b data-tz="Europe/Zurich">--:--</b></span>
        <span><abbr title="Tokio">TYO</abbr> <b data-tz="Asia/Tokyo">--:--</b></span>
      </span>
      <button class="cart-btn" type="button" data-cart-open aria-label="Warenkorb öffnen">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 8h14l-1.2 12H6.2L5 8Z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M9 8V6a3 3 0 0 1 6 0v2" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>
        <span class="cart-count" data-cart-count>0</span>
      </button>
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="mobile-nav" data-menu>
        <span></span><span></span><span class="sr">Menü</span>
      </button>
    </div>
  </div>
  <nav class="mobile-nav" id="mobile-nav" aria-label="Mobile Navigation" hidden>
    <ul>{''.join(f'<li><a href="{pre}{u}"><span class="mono">0{i+1}</span>{t}</a></li>' for i, (u, t) in enumerate(NAV + [("pages/partner/", "Partner")]))}</ul>
    <p class="mono muted">Im Grüntal 10 · 8405 Winterthur</p>
  </nav>
</header>
<main id="main">
{body}
</main>
{footer(pre)}
{cart_drawer()}
</body>
</html>
"""


def footer(pre):
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="foot-cta">
      <div><p class="eyebrow mono">Newsletter</p>
      <h2 class="h2">Neue Drops zuerst.<br><span class="muted">Kein Spam. Nur Nachtschicht.</span></h2></div>
      <form class="newsletter" action="{SHOP}/contact#newsletter" method="post" accept-charset="UTF-8">
        <input type="hidden" name="form_type" value="customer"><input type="hidden" name="utf8" value="✓">
        <input type="hidden" name="contact[tags]" value="newsletter">
        <label class="sr" for="nl-email">E-Mail-Adresse</label>
        <input id="nl-email" type="email" name="contact[email]" placeholder="deine@email.ch" autocomplete="email" required>
        <button class="btn btn-red" type="submit">Anmelden</button>
      </form>
    </div>
    <div class="foot-grid">
      <div>
        <p class="eyebrow mono">Shop</p>
        <ul>
          <li><a href="{pre}collections/all/#hoodies">Hoodies</a></li>
          <li><a href="{pre}collections/all/#tshirts">T-Shirts</a></li>
          <li><a href="{pre}collections/all/#headwear">Caps &amp; Beanies</a></li>
          <li><a href="{pre}pages/custom/">Custom-Merch</a></li>
          <li><a href="{pre}products/nippon-nites-geschenkgutschein/">Gutscheine</a></li>
        </ul>
      </div>
      <div>
        <p class="eyebrow mono">Nippon Nites</p>
        <ul>
          <li><a href="{pre}pages/brandstory/">Brand Story</a></li>
          <li><a href="{pre}pages/partner/">Partner werden</a></li>
          <li><a href="{pre}pages/faq/">FAQ</a></li>
          <li><a href="{pre}pages/contact/">Kontakt</a></li>
        </ul>
      </div>
      <div>
        <p class="eyebrow mono">Rechtliches</p>
        <ul>
          <li><a href="{SHOP}/policies/shipping-policy">Versand</a></li>
          <li><a href="{SHOP}/policies/refund-policy">Rückgabe</a></li>
          <li><a href="{SHOP}/pages/widerruf-formular">Widerruf</a></li>
          <li><a href="{SHOP}/policies/terms-of-service">AGB</a></li>
          <li><a href="{SHOP}/policies/privacy-policy">Datenschutz</a></li>
          <li><a href="{SHOP}/policies/legal-notice">Impressum</a></li>
        </ul>
      </div>
      <address>
        <p class="eyebrow mono">Headquarter</p>
        <p>Nippon Nites<br>{BRAND['street']}<br>{BRAND['zip']} {BRAND['city']} {BRAND['region']}<br>Schweiz</p>
        <p><a href="mailto:{BRAND['email']}">{BRAND['email']}</a></p>
        <p class="socials"><a href="{BRAND['instagram']}" rel="noopener" target="_blank">Instagram ↗</a> <a href="{BRAND['tiktok']}" rel="noopener" target="_blank">TikTok ↗</a></p>
      </address>
    </div>
    <div class="foot-word">{word("foot-logo")}</div>
    <div class="foot-base mono">
      <span>© {date.today().year} Nippon Nites · Winterthur × Tokyo</span>
      <span class="pay">TWINT · PayPal · Visa · Mastercard</span>
      <a href="#top">Nach oben ↑</a>
    </div>
  </div>
</footer>"""


def cart_drawer():
    return """<div class="drawer" data-drawer hidden>
  <div class="drawer-scrim" data-cart-close></div>
  <aside class="drawer-panel" role="dialog" aria-modal="true" aria-labelledby="cart-title">
    <header class="drawer-head">
      <h2 id="cart-title" class="h4">Warenkorb <span class="mono muted" data-cart-count-label></span></h2>
      <button class="icon-btn" type="button" data-cart-close aria-label="Warenkorb schliessen">✕</button>
    </header>
    <div class="drawer-body" data-cart-items></div>
    <footer class="drawer-foot">
      <div class="row"><span>Zwischensumme</span><strong data-cart-total>CHF 0.00</strong></div>
      <p class="mono small muted">Versand &amp; Rabatte im Checkout · TWINT, PayPal &amp; Karte</p>
      <a class="btn btn-red btn-block" data-checkout href="#">Zur Kasse</a>
    </footer>
  </aside>
</div>
<div class="toast" data-toast role="status" aria-live="polite"></div>"""


# ---------------------------------------------------------------- components

def card(p, pre, sizes="(min-width: 1100px) 25vw, (min-width: 700px) 33vw, 50vw", eager=False):
    im = p["images"]
    a = img(im[0]["src"], f"{p['title']} – {p['cat']} von Nippon Nites", sizes, im[0]["w"], im[0]["h"], eager, "pc-img")
    b = img(im[1]["src"], "", sizes, im[1]["w"], im[1]["h"], False, "pc-img pc-alt") if len(im) > 1 and "size-img" not in im[1]["src"] else ""
    price = (f"ab {chf(p['min'])}" if p["min"] != p["max"] else chf(p["min"]))
    badge = ""
    if p["cat_slug"] == "custom":
        badge = '<span class="badge badge-red">Custom</span>'
    elif "Limited" in p["tags"] or "LIMITED" in p["title"]:
        badge = '<span class="badge">Limited</span>'
    elif p["created"] >= "2026-09-01":
        badge = '<span class="badge">Neu</span>'
    return f"""<article class="pc" data-cat="{p['cat_slug']}" data-price="{p['min']}" data-date="{p['created']}">
  <a class="pc-link" href="{pre}products/{p['handle']}/">
    <div class="pc-media">{a}{b}{badge}</div>
    <div class="pc-meta">
      <span class="pc-cat mono">{e(p['cat'])}</span>
      <h3 class="pc-title">{e(p['title'])}</h3>
      <span class="pc-price">{price}</span>
    </div>
  </a>
</article>"""


def hero_mark():
    # Logo-Emblem, dessen drei Streifen sich als "Strassenmarkierung" über die ganze Breite ziehen
    rects = "".join(
        f'<rect class="lane lane-{i}" x="-6000" y="{y}" width="{6000 + x0}" height="{h}"/>'
        for i, (y, h, x0) in enumerate([(893, 53, 20), (1086, 53, 84), (1280, 53, 216)]))
    return f"""<svg class="hero-mark" viewBox="0 0 1569 1554" fill="currentColor" fill-rule="evenodd" aria-hidden="true" overflow="visible">
  <defs><linearGradient id="lane-fade" gradientUnits="userSpaceOnUse" x1="-1100" y1="0" x2="60" y2="0"><stop offset="0" stop-color="currentColor" stop-opacity="0"/><stop offset=".6" stop-color="currentColor" stop-opacity=".12"/><stop offset="1" stop-color="currentColor" stop-opacity=".9"/></linearGradient></defs>
  <g fill="url(#lane-fade)">{rects}</g>
  <g class="hero-wheel">{MARK_PATH}</g>
</svg>"""


# ---------------------------------------------------------------- pages

def build_home(products):
    pre = ""
    by = {p["handle"]: p for p in products}
    niko = by.get("wheelhead-niko-premium") or products[0]
    drops = [p for p in products if p["cat_slug"] not in ("custom", "gutscheine")][:8]
    custom_h = by.get("custom-hoodie-t-shirt")
    custom_t = by.get("custom-t-shirt")
    cats = []
    for slug in ["hoodies", "tshirts", "headwear", "accessoires"]:
        ps = [p for p in products if p["cat_slug"] == slug]
        if not ps:
            continue
        cats.append((slug, ps[0]["cat"], len(ps), ps[0]))
    cat_html = "".join(f"""<a class="cat" href="collections/all/#{s}">
      <span class="cat-n mono">{i+1:02d}</span>
      <span class="cat-media">{img(p['images'][0]['src'], '', '(min-width: 900px) 25vw, 50vw', cls='cat-img', widths=(300, 480, 640, 900))}</span>
      <span class="cat-name">{e(n)}</span><span class="cat-count mono">{c} {"Teil" if c == 1 else "Teile"} →</span></a>"""
                       for i, (s, n, c, p) in enumerate(cats))
    faqs = [q for _, qs in FAQ for q in qs][:4]

    body = f"""
<section class="hero">
  <div class="wrap hero-in">
    <div class="hero-copy">
      <p class="eyebrow mono reveal"><span class="dot"></span>Est. 2024 · Winterthur, Schweiz</p>
      <h1 class="display reveal">JDM&#8209;Streetwear <span class="line">für die <em>Nacht.</em></span></h1>
      <p class="lead reveal">Hoodies, T-Shirts und Custom-Merch mit deinem Auto – jedes Motiv von Hand gezeichnet in Winterthur. Kein Stock-Design, keine KI.</p>
      <div class="cta-row reveal">
        <a class="btn btn-red" href="collections/all/">Alle Drops ansehen</a>
        <a class="btn btn-ghost" href="pages/custom/">Dein Auto als Shirt <span aria-hidden="true">→</span></a>
      </div>
      <dl class="hero-facts mono reveal">
        <div><dt>Bezahlen</dt><dd>TWINT · PayPal · Karte</dd></div>
        <div><dt>Rückgabe</dt><dd>14 Tage</dd></div>
        <div><dt>Versand</dt><dd>CH · DE · AT · weltweit</dd></div>
      </dl>
    </div>
    <div class="hero-art">{hero_mark()}<span class="jp" lang="ja" aria-hidden="true">ニッポンナイツ</span></div>
  </div>
  <a class="scroll-cue mono" href="#drops" aria-label="Zu den Drops scrollen"><span></span>Scroll</a>
</section>

<div class="ticker" aria-hidden="true"><div class="ticker-track">
  {"".join(f"<span>{t}</span><i>✕</i>" for t in ["Hand-illustriert", "Kein KI", "On-Demand produziert", "TWINT · PayPal · Karte", "Brand aus Winterthur", "Passion is not a crime"] * 2)}
</div></div>

<section class="feature wrap" aria-labelledby="niko-h">
  <div class="feature-media reveal">
    {img(niko['images'][0]['src'], f"{niko['title']} T-Shirt – Rückenmotiv Maskottchen Niko", '(min-width: 900px) 50vw, 100vw', niko['images'][0]['w'], niko['images'][0]['h'], widths=(480, 720, 960, 1200))}
    <span class="tag mono">Drop 10/26</span>
  </div>
  <div class="feature-copy">
    <p class="eyebrow mono">01 — Unser Maskottchen</p>
    <h2 id="niko-h" class="h1">Wheelhead <span class="red">Niko</span></h2>
    <p class="lead">Niko ist das Gesicht von Nippon Nites – halb Felge, halb Gang-Mitglied. Auf 280&nbsp;g/m² Heavyweight-Baumwolle, im Boxy-Fit.</p>
    <div class="compare">
      <a class="compare-item" href="products/wheelhead-niko-light/">
        <span class="mono">Light</span><strong>Rückenmotiv gedruckt</strong><span class="price">{chf(by['wheelhead-niko-light']['min']) if 'wheelhead-niko-light' in by else ''}</span>
      </a>
      <a class="compare-item is-hot" href="products/wheelhead-niko-premium/">
        <span class="mono">Premium</span><strong>Komplett gestickt</strong><span class="price">{chf(niko['min'])}</span>
      </a>
    </div>
  </div>
</section>

<section class="section" id="drops" aria-labelledby="drops-h">
  <div class="wrap">
    <div class="section-head">
      <div><p class="eyebrow mono">02 — Shop</p><h2 id="drops-h" class="h1">Neueste Drops</h2></div>
      <a class="link-arrow" href="collections/all/">Alle {len(products)} Produkte <span aria-hidden="true">→</span></a>
    </div>
  </div>
  <div class="rail" data-rail tabindex="0" aria-label="Neueste Produkte – horizontal scrollen">
    {"".join(card(p, pre, "(min-width: 1100px) 22vw, (min-width: 700px) 36vw, 72vw") for p in drops)}
  </div>
  <div class="wrap rail-ctrl"><button class="icon-btn" data-rail-prev aria-label="Zurück">←</button><span class="rail-bar"><span data-rail-progress></span></span><button class="icon-btn" data-rail-next aria-label="Weiter">→</button></div>
</section>

<section class="custom-band" aria-labelledby="custom-h">
  <div class="wrap custom-in">
    <div class="custom-copy">
      <p class="eyebrow mono">03 — Custom-Merch</p>
      <h2 id="custom-h" class="h1">Dein Auto.<br>Von Hand<br>gezeichnet.</h2>
      <p class="lead">Schick uns Fotos von deinem Build – Fabio illustriert ihn als Einzelstück auf Hoodie oder T-Shirt. Jedes Auto, jede Marke.</p>
      <ol class="steps">
        <li><span class="mono">01</span><div><strong>Bestellen</strong><p>Hoodie oder Shirt wählen, Stickerei am Ärmel optional.</p></div></li>
        <li><span class="mono">02</span><div><strong>Fotos schicken</strong><p>Wir melden uns per Mail und besprechen deine Idee.</p></div></li>
        <li><span class="mono">03</span><div><strong>Unikat erhalten</strong><p>Handillustration, Freigabe, Produktion &amp; Versand.</p></div></li>
      </ol>
      <div class="cta-row">
        <a class="btn btn-red" href="pages/custom/">Custom konfigurieren</a>
        <span class="mono muted">T-Shirt ab {chf(custom_t['min']) if custom_t else ''} · Hoodie ab {chf(custom_h['min']) if custom_h else ''}</span>
      </div>
    </div>
    <div class="custom-media">
      {img(custom_h['images'][0]['src'] if custom_h else niko['images'][0]['src'], 'Beispiel: handgezeichneter Custom-Hoodie mit Kundenauto', '(min-width: 900px) 40vw, 100vw', widths=(420, 640, 860, 1100), cls='cm-a')}
      {img(custom_t['images'][0]['src'] if custom_t else niko['images'][1]['src'], 'Beispiel: Custom-T-Shirt mit illustriertem Auto', '(min-width: 900px) 25vw, 60vw', widths=(300, 460, 640, 860), cls='cm-b')}
    </div>
  </div>
</section>

<section class="section wrap" aria-labelledby="cats-h">
  <div class="section-head"><div><p class="eyebrow mono">04 — Kategorien</p><h2 id="cats-h" class="h1">Was suchst du?</h2></div></div>
  <div class="cats">{cat_html}</div>
</section>

<section class="story-band" aria-labelledby="story-h">
  <div class="wrap story-in">
    <div class="story-time mono" aria-hidden="true"><span>00:00</span><span class="bar"></span><span>05:00</span></div>
    <p class="eyebrow mono">05 — Die Marke</p>
    <h2 id="story-h" class="quote" data-words>„Mein Vater schraubt seit über 20&nbsp;Jahren an Autos. Ich zeichne sie – für alle, die nachts noch eine Runde drehen.“</h2>
    <div class="story-sign">
      <div><strong>Fabio Berta</strong><span class="mono muted">Gründer · fährt einen 1992 Toyota Celica T18</span></div>
      <a class="link-arrow" href="pages/brandstory/">Die ganze Story <span aria-hidden="true">→</span></a>
    </div>
  </div>
</section>

<section class="section wrap trust" aria-label="Darum Nippon Nites">
  <div class="trust-item"><span class="trust-n">01</span><h3>Von Hand illustriert</h3><p>Jedes Motiv entsteht auf dem Zeichenbrett in Winterthur – nicht in einem Bildgenerator.</p></div>
  <div class="trust-item"><span class="trust-n">02</span><h3>Auf Bestellung produziert</h3><p>Keine Lagerberge, keine Überproduktion. Dein Teil wird für dich gedruckt oder gestickt.</p></div>
  <div class="trust-item"><span class="trust-n">03</span><h3>Bezahlen wie du willst</h3><p>TWINT, PayPal oder Karte. 14 Tage Rückgaberecht auf alle Standard-Produkte.</p></div>
  <div class="trust-item"><span class="trust-n">04</span><h3>Aus der Szene</h3><p>Gegründet von einem Celica-Fahrer – für Meets, Night Drives und alle mit Benzin im Blut.</p></div>
</section>

<section class="section wrap faq-teaser" aria-labelledby="faq-h">
  <div class="section-head"><div><p class="eyebrow mono">06 — Fragen</p><h2 id="faq-h" class="h1">Kurz erklärt</h2></div><a class="link-arrow" href="pages/faq/">Alle Fragen <span aria-hidden="true">→</span></a></div>
  <div class="acc">{"".join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs)}</div>
</section>
"""
    return page(path="", title="Nippon Nites – JDM Merch & Streetwear aus der Schweiz",
                desc="JDM-Streetwear aus Winterthur: Hoodies, T-Shirts, Caps und Custom-Merch mit deinem Auto – jedes Design von Hand gezeichnet. Zahlung mit TWINT, PayPal & Karte.",
                canonical=f"{SITE}/", body=body, body_class="home",
                schema=[{"@type": "WebPage", "@id": f"{SITE}/#webpage", "url": f"{SITE}/", "name": "Nippon Nites – JDM Merch & Streetwear aus der Schweiz",
                         "isPartOf": {"@id": f"{SITE}/#web"}, "about": {"@id": f"{SITE}/#org"}, "inLanguage": "de-CH"}])


def build_shop(products):
    depth = 2
    pre = "../" * depth
    counts = {}
    for p in products:
        counts[p["cat_slug"]] = (p["cat"], counts.get(p["cat_slug"], (None, 0))[1] + 1)
    chips = [f'<button class="chip is-on" data-filter="all" aria-pressed="true">Alle <span>{len(products)}</span></button>']
    for slug in CAT_ORDER:
        if slug in counts:
            n, c = counts[slug]
            chips.append(f'<button class="chip" data-filter="{slug}" aria-pressed="false">{e(n)} <span>{c}</span></button>')
    body = f"""
<section class="page-head wrap">
  {crumbs_html(pre, [("Home", "", ""), ("Shop", "/collections/all", "collections/all/")])}
  <h1 class="display-sm">JDM Merch <span class="muted">&amp; Streetwear</span></h1>
  <p class="lead">Alle Hoodies, T-Shirts, Caps und Accessoires von Nippon Nites – hand-illustriert in Winterthur, produziert auf Bestellung und versendet in die ganze Schweiz, nach Deutschland, Österreich und weltweit.</p>
</section>
<section class="wrap shop" aria-label="Produkte">
  <div class="shop-bar">
    <div class="chips" role="group" aria-label="Nach Kategorie filtern">{''.join(chips)}</div>
    <label class="sort mono"><span>Sortieren</span>
      <select data-sort><option value="new">Neueste</option><option value="asc">Preis ↑</option><option value="desc">Preis ↓</option></select>
    </label>
  </div>
  <p class="mono muted small" data-result-count aria-live="polite">{len(products)} Produkte</p>
  <div class="grid" data-grid>{''.join(card(p, pre, eager=i < 4) for i, p in enumerate(products))}</div>
</section>
<section class="wrap seo-copy">
  <h2 class="h3">JDM-Kleidung aus der Schweiz – mit Herz für die Szene</h2>
  <p>Nippon Nites steht für japanische Autokultur auf Stoff: Drift-Motive, Klassiker wie Supra, Skyline und Celica, und Statements wie „Alles eingetragen“ oder „Passion is not a crime“. Jedes Design wird von Hand gezeichnet, nicht generiert. Du willst dein eigenes Auto auf einem Shirt? Dann schau dir unseren <a href="{pre}pages/custom/">Custom-Merch</a> an.</p>
</section>"""
    item_list = {"@type": "CollectionPage", "@id": f"{SITE}/collections/all#page", "name": "Alle Produkte",
                 "url": f"{SITE}/collections/all", "isPartOf": {"@id": f"{SITE}/#web"},
                 "mainEntity": {"@type": "ItemList", "numberOfItems": len(products), "itemListElement": [
                     {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/products/{p['handle']}", "name": p["title"]}
                     for i, p in enumerate(products)]}}
    return page(path="collections/all/", depth=depth, title="Shop – JDM Hoodies, T-Shirts & Caps | Nippon Nites",
                desc=f"{len(products)} JDM-Designs: Hoodies, T-Shirts, Caps & Accessoires von Nippon Nites aus Winterthur. Hand-illustriert, on-demand produziert, Versand CH/DE/AT.",
                canonical=f"{SITE}/collections/all", body=body,
                schema=[item_list, crumbs_ld([("Home", "/"), ("Shop", "/collections/all")])])


SIZE_NOTE = {
    "Hoodie": "Fällt eher klein aus – im Zweifel eine Grösse grösser.",
    "T-Shirt": "Oversized / Boxy Fit – für normalen Sitz eine Grösse kleiner.",
}


def build_product(p, products):
    depth = 2
    pre = "../" * depth
    url = f"{SITE}/products/{p['handle']}"
    imgs = p["images"]
    gallery = "".join(
        f'<figure class="g-item" id="img-{i}">{img(im["src"], f"{p["title"]} – Ansicht {i + 1}", "(min-width: 900px) 55vw, 100vw", im["w"], im["h"], i == 0, widths=(480, 720, 1000, 1400))}</figure>'
        for i, im in enumerate(imgs))
    thumbs = "".join(
        f'<a class="thumb" href="#img-{i}" aria-label="Bild {i + 1}">{img(im["src"], "", "80px", widths=(120, 160, 240, 320))}</a>'
        for i, im in enumerate(imgs)) if len(imgs) > 1 else ""
    opts = ""
    for oi, o in enumerate(p["options"]):
        btns = "".join(
            f'<label class="opt"><input type="radio" name="opt{oi}" value="{e(v)}"{" checked" if (j == 0 and (len(o["values"]) == 1 or "Grösse" not in o["name"])) else ""}><span>{e(v)}</span></label>'
            for j, v in enumerate(o["values"]))
        guide = ""
        if "Grösse" in o["name"] and any("size-img" in i["src"] for i in imgs):
            idx = next(k for k, i in enumerate(imgs) if "size-img" in i["src"])
            guide = f'<a class="mono small link-u" href="#img-{idx}">Grössentabelle</a>'
        opts += f'<fieldset class="opts" data-opt="{oi}"><legend><span>{e(o["name"])}</span><span class="mono small muted" data-opt-val></span>{guide}</legend><div class="opt-row">{btns}</div></fieldset>'
    note = SIZE_NOTE.get(p["type"], "")
    if p["cat_slug"] == "custom":
        note = "Nach der Bestellung melden wir uns per E-Mail für Fotos deines Autos. Custom-Artikel sind vom Umtausch ausgeschlossen."
    pdata = {"handle": p["handle"], "title": p["title"], "img": cdn(imgs[0]["src"], 240),
             "variants": [{"id": v["id"], "o": [x for x in v["options"] if x is not None], "p": v["price"],
                           "a": v["available"], "t": v["title"]} for v in p["variants"]]}
    price = chf(p["min"]) if p["min"] == p["max"] else f"ab {chf(p['min'])}"
    related = [x for x in products if x["cat_slug"] == p["cat_slug"] and x["handle"] != p["handle"]]
    related += [x for x in products if x not in related and x["handle"] != p["handle"] and x["cat_slug"] != "gutscheine"]
    related = related[:4]
    meta_desc = (p["desc"][:150].rsplit(" ", 1)[0] + " …") if len(p["desc"]) > 155 else p["desc"]
    is_custom = p["cat_slug"] == "custom"

    body = f"""
<div class="wrap">{crumbs_html(pre, [("Home", "", ""), ("Shop", "", "collections/all/"), (p["cat"], "", f"collections/all/#{p['cat_slug']}"), (p["title"], "", "")])}</div>
<section class="wrap pdp" data-product='{e(json.dumps(pdata, separators=(",", ":")))}'>
  <div class="pdp-gallery">
    <div class="gallery" data-gallery>{gallery}</div>
    <div class="thumbs">{thumbs}</div>
  </div>
  <div class="pdp-info">
    <div class="pdp-sticky">
      <p class="eyebrow mono">{e(p['cat'])}{" · Neu" if p['created'] >= "2026-09-01" else ""}</p>
      <h1 class="h1 pdp-title">{e(p['title'])}</h1>
      <p class="pdp-price"><span data-price>{price}</span> <span class="mono small muted">inkl. MwSt.</span></p>
      <form class="buy" data-buy>
        {opts}
        <p class="mono small muted note">{e(note)}</p>
        <div class="buy-row">
          <div class="qty"><button type="button" data-qty="-1" aria-label="Weniger">−</button><input type="number" min="1" max="20" value="1" aria-label="Menge" data-qty-input><button type="button" data-qty="1" aria-label="Mehr">+</button></div>
          <button class="btn btn-red btn-block" type="submit" data-add>In den Warenkorb</button>
        </div>
        <p class="mono small hint" data-hint aria-live="polite"></p>
      </form>
      <ul class="usp mono small">
        <li>{'Handgezeichnetes Unikat · 1–2 Wochen Produktion' if is_custom else 'Auf Bestellung produziert · ca. 10 Tage Lieferzeit'}</li>
        <li>{'Individuell gefertigt · kein Umtausch' if is_custom else '14 Tage Rückgabe · ungetragen mit Etikett'}</li>
        <li>TWINT · PayPal · Karte</li>
      </ul>
      <details class="pdp-acc" open><summary>Beschreibung</summary><div class="rte">{p['body']}</div></details>
      <details class="pdp-acc"><summary>Versand &amp; Rückgabe</summary><div class="rte"><p>Schweiz &amp; Deutschland: 7–12 Werktage. Europa: 10–15 Werktage. Weltweit: 10–20 Werktage – jeweils inkl. Produktion. Tracking-Link per Mail.</p><p>{'Custom-Bestellungen sind vom Umtausch ausgeschlossen.' if is_custom else 'Rückgabe oder Umtausch innerhalb von 14 Tagen.'} <a href="{pre}pages/faq/">Mehr im FAQ</a>.</p></div></details>
      <details class="pdp-acc"><summary>Pflege</summary><div class="rte"><p>Auf links bei max. 30 °C waschen, nicht in den Trockner, Motiv nicht bügeln.</p></div></details>
    </div>
  </div>
</section>
<div class="sticky-buy" data-sticky-buy hidden><div class="wrap"><span><strong>{e(p['title'])}</strong><span class="mono small" data-price>{price}</span></span><button class="btn btn-red" type="button" data-sticky-add>In den Warenkorb</button></div></div>
<section class="section wrap" aria-labelledby="rel-h">
  <div class="section-head"><div><p class="eyebrow mono">Passt dazu</p><h2 id="rel-h" class="h2">Mehr aus der Nachtschicht</h2></div><a class="link-arrow" href="{pre}collections/all/">Zum Shop <span aria-hidden="true">→</span></a></div>
  <div class="grid">{''.join(card(r, pre) for r in related)}</div>
</section>"""

    avail = "https://schema.org/InStock" if p["available"] else "https://schema.org/OutOfStock"
    offer_base = {"priceCurrency": "CHF", "availability": avail, "url": url, "itemCondition": "https://schema.org/NewCondition",
                  "seller": {"@id": f"{SITE}/#org"},
                  "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "CH",
                                              "returnPolicyCategory": "https://schema.org/MerchantReturnNotPermitted"} if is_custom else
                  {"@type": "MerchantReturnPolicy", "applicableCountry": "CH",
                   "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow", "merchantReturnDays": 14,
                   "returnMethod": "https://schema.org/ReturnByMail"}}
    offers = ({"@type": "Offer", "price": f"{p['min']:.2f}", **offer_base} if p["min"] == p["max"] else
              {"@type": "AggregateOffer", "lowPrice": f"{p['min']:.2f}", "highPrice": f"{p['max']:.2f}",
               "offerCount": len(p["variants"]), **offer_base})
    prod_ld = {"@type": "Product", "@id": f"{url}#product", "name": p["title"], "url": url,
               "image": [cdn(i["src"], 1200) for i in imgs[:6]], "description": p["desc"][:5000],
               "brand": {"@type": "Brand", "name": "Nippon Nites"}, "category": p["cat"],
               "sku": str(p["variants"][0]["id"]), "offers": offers}
    if p["type"] in ("T-Shirt", "Hoodie", "Cap", "Beanie"):
        prod_ld["audience"] = {"@type": "PeopleAudience", "suggestedGender": "unisex"}
    return page(path=f"products/{p['handle']}/", depth=depth,
                title=f"{p['title']} – JDM {p['type'] if p['type'] not in ('Custom','Geschenkkarte','Bundle') else p['cat']} | Nippon Nites",
                desc=meta_desc, canonical=url, body=body, og_image=cdn(imgs[0]["src"], 1200), og_type="product",
                head_extra=f'<meta property="product:price:amount" content="{p["min"]:.2f}"><meta property="product:price:currency" content="CHF">\n',
                schema=[prod_ld, crumbs_ld([("Home", "/"), ("Shop", "/collections/all"), (p["title"], f"/products/{p['handle']}")])])


def build_custom(products):
    depth = 2
    pre = "../" * depth
    by = {p["handle"]: p for p in products}
    ch, ct = by["custom-hoodie-t-shirt"], by["custom-t-shirt"]

    def pack(p):
        return {"handle": p["handle"], "title": p["title"], "img": cdn(p["images"][0]["src"], 240),
                "options": [o["name"] for o in p["options"]],
                "variants": [{"id": v["id"], "o": [x for x in v["options"] if x is not None], "p": v["price"],
                              "a": v["available"], "t": v["title"]} for v in p["variants"]]}

    cfg = {"hoodie": pack(ch), "tshirt": pack(ct)}
    sizes = ["S", "M", "L", "XL", "2XL"]
    body = f"""
<section class="page-head wrap custom-head">
  {crumbs_html(pre, [("Home", "", ""), ("Custom-Merch", "", "")])}
  <p class="eyebrow mono"><span class="dot"></span>Get your own</p>
  <h1 class="display">Dein Auto <span class="line">auf <em>Merch.</em></span></h1>
  <p class="lead">Personalisierte Hoodies und T-Shirts mit deinem eigenen Auto – von Hand illustriert in Winterthur. Für JDM-Klassiker, Euro-Builds, Daily oder Projektauto. Jedes Stück existiert genau einmal.</p>
</section>

<section class="wrap configurator" aria-labelledby="cfg-h" data-config='{e(json.dumps(cfg, separators=(",", ":")))}'>
  <div class="cfg-preview">
    <div class="cfg-stage">
      <img data-cfg-img src="{e(cdn(ch['images'][0]['src'], 900))}" width="1200" height="1200" alt="Vorschau Custom-Merch" loading="lazy">
      <span class="cfg-sleeve cfg-l" data-sleeve="l" aria-hidden="true">NN</span>
      <span class="cfg-sleeve cfg-r" data-sleeve="r" aria-hidden="true">NN</span>
    </div>
    <p class="mono small muted">Beispielansicht · dein Motiv wird individuell gezeichnet</p>
  </div>
  <form class="cfg-form" data-cfg-form>
    <h2 id="cfg-h" class="h2">Konfigurieren</h2>
    <fieldset class="opts"><legend><span>01 · Basis</span></legend>
      <div class="opt-row opt-big">
        <label class="opt"><input type="radio" name="base" value="hoodie" checked><span>Hoodie<small>ab {chf(ch['min'])}</small></span></label>
        <label class="opt"><input type="radio" name="base" value="tshirt"><span>T-Shirt<small>ab {chf(ct['min'])}</small></span></label>
      </div>
    </fieldset>
    <fieldset class="opts"><legend><span>02 · Grösse</span></legend>
      <div class="opt-row">{"".join(f'<label class="opt"><input type="radio" name="size" value="{s}"{" checked" if s == "M" else ""}><span>{s}</span></label>' for s in sizes)}</div>
    </fieldset>
    <fieldset class="opts"><legend><span>03 · Stickerei am Ärmel</span><span class="mono small muted">+ CHF 5.00 pro Seite</span></legend>
      <div class="opt-row">{"".join(f'<label class="opt"><input type="radio" name="emb" value="{v}"{" checked" if v == "Keine" else ""}><span>{v}</span></label>' for v in ["Keine", "Links", "Rechts", "Beide"])}</div>
    </fieldset>
    <div class="cfg-total"><span class="mono">Total</span><strong data-cfg-price>{chf(ch['min'])}</strong></div>
    <button class="btn btn-red btn-block" type="submit">In den Warenkorb</button>
    <p class="mono small muted">Nach der Bestellung melden wir uns per Mail – dann schickst du uns Fotos deines Autos.</p>
  </form>
</section>

<section class="section wrap process" aria-labelledby="proc-h">
  <div class="section-head"><div><p class="eyebrow mono">So läuft's</p><h2 id="proc-h" class="h1">Vom Foto zum Unikat</h2></div></div>
  <ol class="process-list">
    <li class="reveal"><span class="pn">01</span><h3>Bestellen</h3><p>Basis, Grösse und Stickerei wählen und bezahlen – mit TWINT, PayPal oder Karte.</p></li>
    <li class="reveal"><span class="pn">02</span><h3>Briefing per Mail</h3><p>Wir melden uns bei dir. Du schickst Fotos deines Autos, Lieblingswinkel, Kennzeichen-Wunsch, Ideen.</p></li>
    <li class="reveal"><span class="pn">03</span><h3>Handillustration</h3><p>Fabio zeichnet dein Auto im Nippon-Nites-Stil. Kein Filter, keine KI – echte Handarbeit. Du gibst frei.</p></li>
    <li class="reveal"><span class="pn">04</span><h3>Produktion &amp; Versand</h3><p>Druck oder Stickerei, Qualitätscheck, ab zu dir. Ca. 1–2 Wochen Produktion plus Versand.</p></li>
  </ol>
</section>

<section class="section wrap trust">
  <div class="trust-item"><span class="trust-n">✕1</span><h3>Unikat-Garantie</h3><p>Dein Design wird nur für dich angefertigt und nicht weiterverkauft.</p></div>
  <div class="trust-item"><span class="trust-n">∞</span><h3>Jede Marke</h3><p>Toyota, Nissan, Honda, Mazda – aber auch BMW, VW, Porsche oder dein Töffli.</p></div>
  <div class="trust-item"><span class="trust-n">↺</span><h3>Persönlicher Kontakt</h3><p>Du sprichst direkt mit dem Designer – nicht mit einem Ticketsystem.</p></div>
</section>

<section class="section wrap faq-teaser" aria-labelledby="cfaq-h">
  <div class="section-head"><div><p class="eyebrow mono">Fragen zu Custom</p><h2 id="cfaq-h" class="h2">Gut zu wissen</h2></div></div>
  <div class="acc">{"".join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in FAQ[2][1])}</div>
</section>"""
    svc = {"@type": "Service", "name": "Custom-Merch mit eigenem Auto", "serviceType": "Personalisierte Kleidung mit Autoillustration",
           "provider": {"@id": f"{SITE}/#org"}, "areaServed": ["CH", "DE", "AT"], "url": f"{SITE}/pages/custom",
           "offers": [{"@type": "Offer", "name": "Custom T-Shirt", "price": f"{ct['min']:.2f}", "priceCurrency": "CHF", "url": f"{SITE}/products/custom-t-shirt"},
                      {"@type": "Offer", "name": "Custom Hoodie", "price": f"{ch['min']:.2f}", "priceCurrency": "CHF", "url": f"{SITE}/products/custom-hoodie-t-shirt"}]}
    return page(path="pages/custom/", depth=depth, title="Custom Merch mit deinem Auto – Hoodie & T-Shirt | Nippon Nites",
                desc=f"Dein eigenes Auto auf Hoodie oder T-Shirt – von Hand illustriert in Winterthur. Custom T-Shirt ab {chf(ct['min'])}, Hoodie ab {chf(ch['min'])}. Versand CH, DE, AT.",
                canonical=f"{SITE}/pages/custom", body=body,
                schema=[svc, crumbs_ld([("Home", "/"), ("Custom-Merch", "/pages/custom")])])


def build_story():
    depth = 2
    pre = "../" * depth
    body = f"""
<section class="page-head wrap">
  {crumbs_html(pre, [("Home", "", ""), ("Brand Story", "", "")])}
  <p class="eyebrow mono">Established in the dark · Winterthur × Tokyo</p>
  <h1 class="display">Passion is <span class="line">not a <em>crime.</em></span></h1>
</section>

<section class="wrap night">
  <ol class="night-line">
    <li class="reveal"><time class="mono">00:00</time><p>Das Parkhaus ist leer, die Motoren noch warm. Hier beginnt Nippon Nites.</p></li>
    <li class="reveal"><time class="mono">01:30</time><p>Inspiriert von Nächten auf der Shuto Expressway <span lang="ja">首都高</span> und dem Neonlicht Akihabaras.</p></li>
    <li class="reveal"><time class="mono">03:00</time><p>Ein Bleistift, ein Blatt, eine Celica. Jedes Design startet als Handzeichnung.</p></li>
    <li class="reveal"><time class="mono">05:00</time><p>Morgengrauen in Winterthur. Das Motiv geht in Produktion – für dich.</p></li>
  </ol>
</section>

<section class="section wrap founder" aria-labelledby="founder-h">
  <div class="founder-card reveal">
    <div class="founder-mark">{mark("fm")}</div>
    <dl class="mono small">
      <div><dt>Gründer</dt><dd>Fabio Berta</dd></div>
      <div><dt>Gegründet</dt><dd>2024</dd></div>
      <div><dt>Base</dt><dd>Winterthur ZH</dd></div>
      <div><dt>Daily</dt><dd>1992 Toyota Celica T18</dd></div>
    </dl>
  </div>
  <div class="founder-copy">
    <p class="eyebrow mono">Über den Gründer</p>
    <h2 id="founder-h" class="h1">Fabio Berta</h2>
    <div class="rte big">
      <p>Ich bin Fabio Berta aus Winterthur. Meine Begeisterung für Autos begann schon als Kind – mein Vater arbeitet seit über 20 Jahren als Mechaniker.</p>
      <p>Heute fahre ich einen <strong>1992 Toyota Celica T18</strong> und habe 2024 Nippon Nites gegründet: eine Marke, die die Liebe zur JDM-Kultur und zur japanischen Nachtkultur vereint.</p>
      <p><strong>Nippon</strong> heisst auf Japanisch „Japan“, <strong>Nites</strong> steht für „Nights“ – das besondere Flair der nächtlichen Tuning-Szene.</p>
      <p>Unsere Designs, ob Custom oder Drop, sind in der Schweiz einzigartig. Jedes Motiv wird von Hand illustriert – wir arbeiten bewusst nicht mit künstlicher Intelligenz. Es geht uns nicht nur ums Verkaufen, sondern darum, die Leidenschaft für JDM weiterzugeben.</p>
    </div>
  </div>
</section>

<section class="section wrap trust">
  <div class="trust-item"><span class="trust-n">01</span><h3>Hand-illustriert</h3><p>Kein KI. Jedes Design entsteht von Hand.</p></div>
  <div class="trust-item"><span class="trust-n">02</span><h3>Bewusste Materialien</h3><p>Bio-Baumwolle und schwere Heavyweight-Qualitäten – Qualität, die man spürt.</p></div>
  <div class="trust-item"><span class="trust-n">03</span><h3>Mit Leidenschaft</h3><p>JDM ist kein Style, sondern ein Lifestyle.</p></div>
</section>

<section class="wrap big-cta">
  <h2 class="display-sm">Join the <em>underground.</em></h2>
  <div class="cta-row"><a class="btn btn-red" href="{pre}collections/all/">Shop the drop</a><a class="btn btn-ghost" href="{pre}pages/contact/">Kontakt</a></div>
</section>"""
    about = {"@type": "AboutPage", "url": f"{SITE}/pages/brandstory", "name": "Brand Story – Nippon Nites",
             "mainEntity": {"@type": "Person", "name": "Fabio Berta", "jobTitle": "Gründer & Designer",
                            "worksFor": {"@id": f"{SITE}/#org"}, "homeLocation": {"@type": "Place", "name": "Winterthur, Schweiz"},
                            "knowsAbout": ["JDM", "Illustration", "Automobil-Tuning", "Streetwear"]}}
    return page(path="pages/brandstory/", depth=depth, title="Brand Story – Fabio Berta & Nippon Nites aus Winterthur",
                desc="Wie Nippon Nites entstand: Gründer Fabio Berta, ein 1992 Toyota Celica T18 und die Liebe zur japanischen Tuning-Kultur. Handgezeichnete JDM-Designs aus Winterthur.",
                canonical=f"{SITE}/pages/brandstory", body=body,
                schema=[about, crumbs_ld([("Home", "/"), ("Brand Story", "/pages/brandstory")])])


def build_faq():
    depth = 2
    pre = "../" * depth
    groups = "".join(f"""<section class="faq-group" id="faq-{i}" aria-labelledby="fg-{i}">
      <h2 id="fg-{i}" class="h3"><span class="mono muted">{i+1:02d}</span> {e(g)}</h2>
      <div class="acc">{"".join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in qs)}</div>
    </section>""" for i, (g, qs) in enumerate(FAQ))
    toc = "".join(f'<li><a href="#faq-{i}">{e(g)}</a></li>' for i, (g, _) in enumerate(FAQ))
    body = f"""
<section class="page-head wrap">
  {crumbs_html(pre, [("Home", "", ""), ("FAQ", "", "")])}
  <h1 class="display-sm">Häufige <span class="muted">Fragen</span></h1>
  <p class="lead">Lieferzeiten, Rückgabe, Custom-Bestellungen und Grössen – alles auf einen Blick. Nicht dabei? Schreib an <a class="link-u" href="mailto:{BRAND['email']}">{BRAND['email']}</a>.</p>
</section>
<div class="wrap faq-layout">
  <nav class="faq-toc mono" aria-label="Themen"><ul>{toc}</ul></nav>
  <div>{groups}</div>
</div>"""
    faq_ld = {"@type": "FAQPage", "url": f"{SITE}/pages/faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for _, qs in FAQ for q, a in qs]}
    return page(path="pages/faq/", depth=depth, title="FAQ – Versand, Rückgabe & Custom-Bestellungen | Nippon Nites",
                desc="Antworten zu Lieferzeit (CH, DE, AT, weltweit), Rückgabe, Grössen, Pflege und Custom-Merch mit deinem Auto bei Nippon Nites.",
                canonical=f"{SITE}/pages/faq", body=body, schema=[faq_ld, crumbs_ld([("Home", "/"), ("FAQ", "/pages/faq")])])


def build_contact():
    depth = 2
    pre = "../" * depth
    body = f"""
<section class="page-head wrap">
  {crumbs_html(pre, [("Home", "", ""), ("Kontakt", "", "")])}
  <h1 class="display-sm">Pit <span class="muted">Stop.</span></h1>
  <p class="lead">Fragen zur Bestellung, Custom-Idee oder Grosshandel? Schreib uns – wir antworten normalerweise innert 48 Stunden.</p>
</section>
<section class="wrap contact">
  <form class="contact-form" action="{SHOP}/contact#contact_form" method="post" accept-charset="UTF-8">
    <input type="hidden" name="form_type" value="contact"><input type="hidden" name="utf8" value="✓">
    <div class="field"><label for="c-name">Name</label><input id="c-name" name="contact[name]" autocomplete="name" required></div>
    <div class="field"><label for="c-mail">E-Mail</label><input id="c-mail" type="email" name="contact[email]" autocomplete="email" required></div>
    <div class="field"><label for="c-sub">Betreff</label>
      <select id="c-sub" name="contact[Betreff]"><option>Bestellstatus</option><option>Versandanfrage</option><option>Custom-Anfrage</option><option>Grosshandel</option><option>Partnerschaft</option><option>Sonstiges</option></select></div>
    <div class="field"><label for="c-msg">Nachricht</label><textarea id="c-msg" name="contact[body]" rows="6" required></textarea></div>
    <button class="btn btn-red" type="submit">Nachricht senden</button>
  </form>
  <aside class="contact-side">
    <div class="info-block"><p class="eyebrow mono">Headquarter</p><address><strong>Nippon Nites</strong><br>{BRAND['street']}<br>{BRAND['zip']} {BRAND['city']} {BRAND['region']}<br>Schweiz</address></div>
    <div class="info-block"><p class="eyebrow mono">Direkt</p><p><a class="link-u" href="mailto:{BRAND['email']}">{BRAND['email']}</a></p></div>
    <div class="info-block"><p class="eyebrow mono">Community</p><p><a class="link-u" href="{BRAND['instagram']}" target="_blank" rel="noopener">Instagram @nipponnites ↗</a><br><a class="link-u" href="{BRAND['tiktok']}" target="_blank" rel="noopener">TikTok @nippon_nites ↗</a></p></div>
    <div class="info-block"><p class="eyebrow mono">Grosshandel</p><p class="muted">Anzahlung 50 %, Lieferzeit 4–6 Wochen je nach Verfügbarkeit. Details besprechen wir persönlich und halten sie im Vertrag fest.</p></div>
  </aside>
</section>"""
    cp = {"@type": "ContactPage", "url": f"{SITE}/pages/contact", "name": "Kontakt – Nippon Nites",
          "mainEntity": {"@id": f"{SITE}/#org"}}
    return page(path="pages/contact/", depth=depth, title="Kontakt – Nippon Nites, Winterthur",
                desc="Kontakt zu Nippon Nites: Im Grüntal 10, 8405 Winterthur. Fragen zu Bestellung, Custom-Merch oder Grosshandel an info@nipponnites.com.",
                canonical=f"{SITE}/pages/contact", body=body, schema=[cp, crumbs_ld([("Home", "/"), ("Kontakt", "/pages/contact")])])


def build_partner():
    depth = 2
    pre = "../" * depth
    body = f"""
<section class="page-head wrap">
  {crumbs_html(pre, [("Home", "", ""), ("Partner", "", "")])}
  <p class="eyebrow mono"><span class="dot"></span>Affiliate-Programm</p>
  <h1 class="display">Werde <span class="line"><em>Partner.</em></span></h1>
  <p class="lead">Du bist Creator, Fotograf, organisierst Meets oder hast einen Club? Teile Nippon Nites mit deiner Community und werde für jede Bestellung über deinen Link belohnt.</p>
</section>
<section class="section wrap process">
  <ol class="process-list">
    <li class="reveal"><span class="pn">01</span><h3>Bewerben</h3><p>Kurz vorstellen: Wer bist du, welche Kanäle, welche Szene.</p></li>
    <li class="reveal"><span class="pn">02</span><h3>Link &amp; Code erhalten</h3><p>Du bekommst deinen persönlichen Link und Rabattcode für deine Follower.</p></li>
    <li class="reveal"><span class="pn">03</span><h3>Teilen</h3><p>Auf Instagram, TikTok, am Meet oder auf dem Club-Shirt.</p></li>
    <li class="reveal"><span class="pn">04</span><h3>Provision kassieren</h3><p>Für jede Bestellung über deinen Link gibt's Provision.</p></li>
  </ol>
</section>
<section class="wrap big-cta">
  <h2 class="display-sm">Bock auf <em>Teamwork?</em></h2>
  <div class="cta-row"><a class="btn btn-red" href="mailto:{BRAND['email']}?subject=Partnerschaft%20Nippon%20Nites">Jetzt bewerben</a><a class="btn btn-ghost" href="{SHOP}/pages/partner">Zum Partner-Portal ↗</a></div>
</section>"""
    return page(path="pages/partner/", depth=depth, title="Partner werden – Affiliate-Programm | Nippon Nites",
                desc="Werde Partner von Nippon Nites: Creator, Car-Clubs und Meet-Organisatoren erhalten Provision auf jede Bestellung über ihren persönlichen Link.",
                canonical=f"{SITE}/pages/partner", body=body, schema=[crumbs_ld([("Home", "/"), ("Partner", "/pages/partner")])])


def build_404():
    body = """
<section class="page-head wrap notfound">
  <p class="eyebrow mono">Fehler 404</p>
  <h1 class="display">Falsch <span class="line"><em>abgebogen.</em></span></h1>
  <p class="lead">Diese Seite gibt es nicht (mehr). Vielleicht ist der Drop ausverkauft – oder der Link hat einen Tippfehler.</p>
  <div class="cta-row"><a class="btn btn-red" data-root-link href="collections/all/">Zum Shop</a><a class="btn btn-ghost" data-root-link href="./">Startseite</a></div>
</section>"""
    # 404 liegt im Root, wird aber auch in Unterordnern ausgeliefert -> absolute Basis per JS
    return page(path="404", title="Seite nicht gefunden | Nippon Nites", desc="Diese Seite existiert nicht.",
                canonical=f"{SITE}/404", body=body, is_404=True)


# ---------------------------------------------------------------- write

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def fetch():
    req = urllib.request.Request(f"{SITE}/products.json?limit=250", headers={"User-Agent": "nn-build"})
    DATA.write_text(urllib.request.urlopen(req, timeout=30).read().decode())
    print("Produktdaten aktualisiert.")


def main():
    if "--fetch" in sys.argv:
        fetch()
    products = load_products()

    for d in ("products", "collections", "pages", "assets"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    shutil.copytree(SRC / "assets", ROOT / "assets")

    write("index.html", build_home(products))
    write("collections/all/index.html", build_shop(products))
    for p in products:
        write(f"products/{p['handle']}/index.html", build_product(p, products))
    write("pages/custom/index.html", build_custom(products))
    write("pages/brandstory/index.html", build_story())
    write("pages/faq/index.html", build_faq())
    write("pages/contact/index.html", build_contact())
    write("pages/partner/index.html", build_partner())
    write("404.html", build_404())
    write(".nojekyll", "")

    today = date.today().isoformat()
    urls = [("/", "1.0", today), ("/collections/all", "0.9", today), ("/pages/custom", "0.9", today),
            ("/pages/brandstory", "0.6", today), ("/pages/faq", "0.6", today), ("/pages/contact", "0.5", today),
            ("/pages/partner", "0.4", today)]
    urls += [(f"/products/{p['handle']}", "0.8", p["updated"]) for p in products]
    img_map = {f"/products/{p['handle']}": p["images"][:3] for p in products}
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for u, pr, lm in urls:
        imgs = "".join(f"<image:image><image:loc>{e(i['src'])}</image:loc></image:image>" for i in img_map.get(u, []))
        sm.append(f"<url><loc>{SITE}{u}</loc><lastmod>{lm}</lastmod><priority>{pr}</priority>{imgs}</url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", ("User-agent: *\nDisallow: /\n# Vorschau – beim Livegang PREVIEW=False setzen\n" if PREVIEW else
                         f"User-agent: *\nAllow: /\nDisallow: /cart\nDisallow: /checkout\nDisallow: /account\n\nSitemap: {SITE}/sitemap.xml\n"))
    write("site.webmanifest", json.dumps({
        "name": "Nippon Nites", "short_name": "Nippon Nites", "start_url": "./", "display": "standalone",
        "background_color": "#0a0a0b", "theme_color": "#0a0a0b",
        "icons": [{"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2))
    print(f"Fertig: {len(products)} Produkte, {len(urls)} URLs.")


if __name__ == "__main__":
    main()
