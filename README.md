# Nippon Nites – Redesign 2026

Statische, SEO-optimierte Neugestaltung von [nipponnites.com](https://nipponnites.com).
Warenkorb und Checkout laufen weiterhin über Shopify (TWINT, PayPal, Karte).

## Vorschau

GitHub → **Settings → Pages** → Source: *Deploy from a branch* → Branch `main`, Ordner `/ (root)`.
Danach ist die Seite unter `https://<user>.github.io/nipponnites-redesign/` erreichbar.

Lokal:

```bash
python3 -m http.server 8000
```

## Bauen

Alle HTML-Seiten werden aus `data/products.json` (Shopify-Export) erzeugt:

```bash
python3 build.py           # aus vorhandenen Daten
python3 build.py --fetch   # vorher aktuelle Produkte von nipponnites.com laden
```

| Ordner/Datei | Inhalt |
|---|---|
| `build.py` | Generator: Templates, Texte, FAQ, Schema.org |
| `src/assets/` | `style.css`, `app.js`, Logos (SVG aus den Original-Logos vektorisiert) |
| `data/products.json` | Produktdaten |
| `index.html`, `products/`, `collections/`, `pages/` | generierte Seiten (nicht von Hand bearbeiten) |

## SEO nach Google-Richtlinien

- **E-E-A-T:** Gründer, Standort, Handarbeit und Kontaktdaten sind sichtbar und als `Organization` / `Person` ausgezeichnet.
- **Strukturierte Daten:** `Product` + `Offer` inkl. Rückgaberichtlinie, `BreadcrumbList`, `FAQPage`, `ItemList`, `Service`, `WebSite`.
- **Core Web Vitals:** kein Framework, CSS ca. 9 KB und JS ca. 5 KB (gzip), responsive Bilder via Shopify-CDN, Lazy Loading, feste Bildgrössen (kein Layout-Shift).
- **Gleiche URLs wie Shopify** (`/products/…`, `/collections/all`, `/pages/…`): Beim Livegang gehen keine Rankings verloren.
- Eindeutige Titles und Descriptions, `canonical`, `hreflang de-CH`, Open Graph, Bild-Sitemap.
- Lokales SEO: Adresse in Winterthur, `geo`-Meta, Liefergebiete CH/DE/AT.

**Wichtig:** Die Vorschau ist auf `noindex` gesetzt (`PREVIEW = True` in `build.py`), damit Google sie nicht als
Duplicate Content wertet. Beim Livegang `PREVIEW = False` setzen und neu bauen.

## Aktionsleiste

`PROMO` in `build.py` ändern oder leeren.
