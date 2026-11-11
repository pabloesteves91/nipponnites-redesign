# Nippon Nites – Redesign V2 «Skizzenbuch» als Shopify-Theme

## Context

Version 1 (statische Seite in diesem Repo, dunkel + Rot + Blockschrift) wurde abgelehnt: wirkt nach KI/Template,
zu kalt, zu wenig Bewegung. Fabio will ein komplett neues Design, das **authentisch und einladend** wirkt, mit
**erzählender Motion**, und das als **echtes Shopify-Theme** läuft. Der Plan wird danach von einem anderen Modell
(Opus) 1:1 umgesetzt, er muss also ohne Rückfragen ausführbar sein.

Entscheide aus der Fragerunde:

| Thema | Entscheid |
|---|---|
| Stil | Skizzenbuch / Werkstatt: warmes Papier, Bleistift, Marker, Klebeband, Polaroids |
| Motion | Erzählend (Scroll-Story, selbstzeichnende Linien), aber schnell |
| Fotos | Fabio liefert: er + Celica, Kunden & Meets. Bis dahin Platzhalter |
| «Google-Formel XYZ» | Gibt es für die Suche nicht. Umgesetzt wird **beides**: Googles Such-Richtlinien **und** Texte nach XYZ-Muster («X erreicht, gemessen an Y, durch Z») |
| Neue Inhalte | Kunden-Galerie |
| Tonfall | Wir-Form, locker, Schweizer Schreibweise (ss statt ß), wenig Englisch |
| Ziel | Echtes Shopify-Theme |
| **Harte Vorgabe** | **Die Live-Seite darf nicht verändert werden** |

Ehrlicher Hinweis für die Übergabe an Fabio: Kein Design garantiert Traffic oder ein Top-Ranking. Der Plan setzt um,
was Google nachweislich bewertet (hilfreiche Inhalte, Vertrauen, Tempo, saubere Daten).

## Ausgangslage (bereits geprüft, nur gelesen)

- Shopify-Konnektor ist mit dem Shop verbunden (Nippon Nites, Plan Basic, CHF). Theme-Mutationen sind vorhanden:
  `themeDuplicate`, `themeFilesUpsert` (max. 50 Dateien pro Aufruf), `themePublish` (**verboten**).
- Live-Theme: `nipponnitestheme/main`, ID `gid://shopify/OnlineStoreTheme/185559548179`, Rolle MAIN,
  zuletzt geändert `2026-11-04T23:14:21Z`. Eigenes kleines Theme mit 48 Dateien:
  - `layout/theme.liquid` (Meta, Open Graph, Organization-JSON-LD, lädt `theme.min.css` = vorkompiliertes Tailwind,
    Google Fonts Space Grotesk/Inter, Material-Symbols-Iconfont, `global.js`)
  - 23 Sections (`header`, `footer`, `ticker-bar`, `announcement-bar`, `hero-product`, `hero`, `featured-duo`,
    `featured-collection`, `trust-strip`, `passion-banner`, `main-collection`, `main-product` (23 KB),
    `product-cross-sell`, `product-reviews`, `main-search`, `page-brand-story`, `page-contact`, `page-custom`,
    `page-faq`, `page-oberteile`, `page-partner`, `page-sitemap`, `page-widerruf`)
  - Snippets `cart-drawer`, `star-rating`; 13 Templates (JSON); Apps: Judge.me (App-Block in `settings_data.json`),
    UpPromote (`uppromote.css`, Partner-Seite)
- Bestehende Entwürfe `…Entwurf (Claude)` und `…Startseite Test (Claude)`: **nicht anfassen**.
- Dieses Repo enthält V1 (statischer Generator `build.py`). Wiederverwendbar daraus:
  `src/assets/logo-mark.svg`, `logo-word.svg`, `logo.svg` (vektorisiertes Logo mit `currentColor`, funktioniert
  schwarz auf Papier) und die FAQ-Texte in `build.py` (Liste `FAQ`).

## Sicherheitsregeln (gelten für jede Phase)

1. Erster Schritt: `themeDuplicate(id: 185559548179, name: "Nippon Nites – V2 Skizzenbuch (Claude)")`.
   Die zurückgegebene ID ist die **einzige** Theme-ID, auf die geschrieben wird. In `theme/THEME_ID.txt` festhalten.
2. Nie `themePublish`, nie `themeDelete`, nie `themeFilesUpsert`/`themeFilesDelete` mit ID `…185559548179`.
3. Keine Änderungen an Shop-Daten: keine Produkte, Seiten, Menüs, Rabatte, Dateien, Metafelder. Nur Theme-Dateien
   der Kopie. Ausnahme gibt es keine; was Shop-Daten braucht, kommt auf die Liste «Schritte für den Livegang».
4. Checkout im Test nie abschliessen (in den Warenkorb legen ist erlaubt).
5. Am Ende jeder Phase prüfen: Live-Theme hat weiterhin Rolle MAIN und `updatedAt` der Dateien ist unverändert.

## Arbeitsweise

- Alle 48 Dateien der Kopie per `theme(id).files { filename body { … content } }` lesen und nach `theme/` in dieses
  Repo schreiben (gleiche Ordnerstruktur). Unverändert committen = Baseline.
- Lokal in `theme/` bearbeiten, dann geänderte Dateien per `themeFilesUpsert` (Body-Typ TEXT, SVG als TEXT) in die
  Kopie laden. Nach jedem Upload `userErrors` prüfen (Liquid-Fehler werden dort gemeldet).
- Vorschau: `https://nipponnites.com/?preview_theme_id=<numerische ID>`.
- V1-Dateien im Repo-Root bleiben liegen (kein Aufräumen in diesem Auftrag). Commit und Push auf den Branch, den
  die Sitzung vorgibt.
- Vor Phase 1 Skill `frontend-design:frontend-design` laden; nach Phase 2 `design:design-critique`;
  Texte mit `design:ux-copy`; in Phase 6 `marketing:seo-audit`, `design:accessibility-review`, `ponytail:ponytail-review`.
- **Keine KI-Bilder oder -Videos** (Higgsfield, Canva-Generierung, Figma-Generierung bleiben ungenutzt): Die Marke
  wirbt mit «kein KI», generierte Bilder wären ein Widerspruch. Konnektoren im Einsatz: Shopify (Theme),
  Playwright (Prüfung).

### Regeln beim Umbau einer Section

Jede Section zuerst vollständig lesen. Erhalten bleiben: Liquid-Logik, alle `{% schema %}`-Setting-IDs und
Block-Typen (sonst brechen `settings_data.json` und die Template-JSONs), Formular-`action`s und Feldnamen,
IDs/`data-`Attribute/Funktionsnamen, die `assets/global.js` und `snippets/cart-drawer.liquid` benutzen
(z. B. `openCartDrawer()`, `data-cart-count`, `#mobile-menu-btn`, `#mobile-nav`), Judge.me- und UpPromote-Einbindungen,
der komplette Rechtstext und alle Formularfelder in `page-widerruf`. Ersetzt werden nur Markup-Klassen
(Tailwind-Utilities → eigene `nn-`Klassen) und Texte.

## Designsystem «Skizzenbuch»

Neue Dateien: `assets/nn.css`, `assets/nn.js`, `assets/nn-logo-mark.svg`, `assets/nn-logo-word.svg` (aus `src/assets/`).

**Farben** (CSS-Variablen in `:root`, zusätzlich als Farbfelder in `settings_schema.json`):

| Token | Wert | Einsatz |
|---|---|---|
| `--papier` | `#F4EFE4` | Seitenhintergrund |
| `--karton` | `#E7DFCC` | Karten, Produktkacheln, Footer |
| `--tinte` | `#1E1B17` | Text, Logo, Linien |
| `--graphit` | `#6E675D` | Nebentext, Bleistift-Linien |
| `--marker` | `#D7351F` | Akzent, Hervorhebungen, primäre Buttons |
| `--blaustift` | `#2D4E86` | handschriftliche Randnotizen, Pfeile |
| `--tape` | `#E8C76A` bei 70 % Deckkraft | Klebeband-Ecken |

Kontrast prüfen: Text auf Papier mindestens 4.5:1 (Marker-Rot nur für grosse Schrift oder als Fläche mit weisser Schrift).

**Schrift** (Google Fonts, `display=swap`, ein einziger `<link>`):
- Überschriften: **Barlow Condensed** 600/800, Versalien, leicht gesperrt (erinnert an Strassenschilder und Startnummern)
- Fliesstext: **Barlow** 400/500, 17 px, Zeilenhöhe 1.6
- Handnotizen: **Reenie Beanie**, nur für kurze Randbemerkungen (max. 2 pro Bildschirm), immer `--blaustift`
- Material-Symbols-Iconfont und Space Grotesk/Inter entfallen. Icons: wenige handgezeichnete Inline-SVGs.

**Material-Details** (alles CSS/SVG, keine Bilddateien):
- Papierkorn: SVG-`feTurbulence`-Rauschen als Data-URI auf `body`, 4–6 % Deckkraft
- Punktraster wie im Skizzenbuch auf ausgewählten Abschnitten (`radial-gradient`, 1 px Punkt alle 24 px)
- Snippet `nn-scribble.liquid` (Parameter `art`: `unterstrich`, `kreis`, `pfeil`, `haken`, `kreuz`, `stern`):
  bewusst unregelmässige, von Hand geschriebene SVG-Pfade mit `pathLength="1"` (für die Zeichen-Animation)
- Snippet `nn-foto.liquid`: Polaroid-Rahmen mit Klebeband-Ecke, leicht gedreht (−1.5° / +1°), handschriftliche
  Bildunterschrift. Ohne Bild: gestrichelter Rahmen mit Notiz «Foto folgt» (kein Stockfoto, kein KI-Bild)
- Snippet `nn-stempel.liquid`: gedrehter Stempel mit rauem Rand («Kein KI», «1 von 1», «Neu»)
- Buttons: rechteckig, 2 px Tintenlinie, primär = Marker-Fläche; beim Klick 1 px «eingedrückt»
- Keine Farbverläufe, kein Glas-Effekt, keine Leucht-Schatten, keine Emojis.

**Motion** (`assets/nn.js`, ohne Bibliothek, Ziel unter 8 KB; alles hinter `prefers-reduced-motion` abschaltbar):
1. Linien zeichnen sich selbst: `stroke-dashoffset` 1 → 0, sobald das Element sichtbar wird (IntersectionObserver)
2. Marker-Hervorhebung fährt hinter Schlüsselwörter (`background-size` 0 → 100 %)
3. Polaroids «fallen» aufs Blatt: aus zufälligem Winkel in die Endlage, leichtes Überschwingen
4. Checkliste hakt sich nacheinander ab
5. Scroll-Story «Vom Foto zum Unikat»: ein Scroll-Handler setzt `--p` (0–1) auf dem fixierten Abschnitt;
   CSS blendet damit vier Ebenen per `clip-path` ineinander (Foto → Bleistiftskizze → Farbe → fertiges Shirt)
6. Produktkarte hebt sich beim Hover wie ein Blatt (−1° Drehung, weicher Schatten), zweites Bild blendet ein
7. Seitenwechsel: `@view-transition { navigation: auto; }`
8. Klebeband-Laufstreifen statt Ticker (pausiert beim Hover)

## Seiten und Abschnitte

**Global**
- `layout/theme.liquid`: neue Fonts, `nn.css`, `nn.js`; `theme.min.css` bleibt bis Phase 6 geladen (noch nicht
  umgebaute Sections funktionieren so weiter), danach entfernen. Skip-Link ergänzen.
- `header`: Papier, schwarzes Logo (SVG-Asset; Bild-Setting bleibt als Alternative), Menü aus `linklists`,
  aktiver Punkt mit Scribble-Unterstrich, Warenkorb-Zähler als roter Stempelpunkt.
- `ticker-bar` / `announcement-bar`: Klebeband-Streifen, Text weiter aus den Settings.
- `footer`: Karton, grosses Wortlogo, Newsletter (bestehendes Shopify-Formular), Adresse, Rechtliches, Social.
- `cart-drawer`: gleiche Logik, neues Kleid («Notizzettel»).

**Startseite** (`templates/index.json`, bestehende Section-Typen bleiben, neue kommen dazu)
1. `hero` neu: H1 «JDM-Merch, von Hand gezeichnet.» (Scribble unter «von Hand»), Text nach XYZ:
   «Dein Auto als Unikat auf Hoodie oder Shirt, in 1–2 Wochen, gezeichnet in Winterthur statt von einer KI generiert.»
   Buttons «Dein Auto zeichnen lassen» / «Drops ansehen». Rechts Collage aus 3 `nn-foto` (Bild-Settings:
   Fabio beim Zeichnen, Celica, Kundenshirt) mit Blaustift-Pfeilen. Stempel «Kein KI».
2. `trust-strip`: handgeschriebene Checkliste (TWINT/PayPal/Karte, 14 Tage Rückgabe, kein KI, aus Winterthur).
3. **Neu** `nn-prozess`: Scroll-Story in 4 Schritten, je Schritt ein Bild-Setting, endet mit Button zur Custom-Seite.
4. `featured-collection`: «Neue Drops», 8 Produkte, Judge.me-Sterne über `star-rating`.
5. `hero-product`: Niko, Vergleich Light / Premium.
6. **Neu** `nn-galerie` (Teaser, 6 Polaroids) mit Link zur Galerie.
7. **Neu** `nn-ueber-uns`: Foto Fabio + Celica, drei Sätze, Unterschrift, Link zur Story.
8. `passion-banner`: «Passion is not a crime.» als Marker-Schriftzug, der sich zeichnet.
9. `featured-duo` bleibt als Option im Editor, in der Reihenfolge deaktiviert.

**Produkt** (`main-product`, `product-cross-sell`, `product-reviews`): Galerie auf Karton, Varianten als Kästchen,
Brotkrumen, Aufklapper «Versand & Rückgabe» und «Pflege», auf dem Handy fixierte Kaufleiste nur falls schon vorhanden.
Varianten-, Preis- und Warenkorb-Logik unverändert.

**Kollektion / Suche** (`main-collection`, `main-search`, `page-oberteile`, `collection.custom`): Raster mit
`nn-`Produktkarte (ein gemeinsames Snippet `nn-produktkarte.liquid` für alle Raster), bestehende Filter/Sortierung behalten.

**Custom** (`page-custom`): H1 «Dein Auto auf Merch», `nn-prozess` wiederverwenden, zwei Karten «Custom T-Shirt» /
«Custom Hoodie» mit «ab»-Preis und Link zum Produkt (kein eigener Konfigurator; die Produktseite kann das schon),
Galerie-Teaser, Custom-FAQ.

**Kunden-Galerie** (neu): Section `nn-galerie` mit Blöcken (Bild, Auto, Kunde optional, Ort optional, Produkt-Link),
Setting `limit` für den Teaser. Neues Template `templates/page.galerie.json`. Alt-Text je Bild:
«Custom-{Produkt} mit {Auto} – Nippon Nites». Die Seite selbst wird erst beim Livegang angelegt (Shop-Daten);
in der Vorschau ist die Galerie über Startseite und Custom-Seite sichtbar.

**Story, FAQ, Kontakt, Partner, Sitemap, Widerruf**: gleiche Inhalte, neues Kleid. Story als Skizzenbuch-Doppelseite
mit Zeitstrahl; FAQ als Aufklapper (Texte aus `build.py` → `FAQ` übernehmen, wo die Live-Seite veraltet ist,
z. B. keine «450 GSM»-Angabe, die nicht zu den Produkten passt); Widerruf nur optisch.
**Neu** `templates/404.json` + Section `nn-404` («Falsch abgebogen»).

**Texte nach XYZ-Muster** (Beispiele, in allen Abschnitten so vorgehen; nur Zahlen verwenden, die der Shop belegt):
- «Jedes Motiv von Hand gezeichnet (X), kein einziges aus dem Bildgenerator (Y), auf dem Zeichenbrett in Winterthur (Z).»
- «Auf Bestellung produziert (X): Lieferung in ca. 10 Tagen (Y), ohne Lagerware und Überproduktion (Z).»
- Keine erfundenen Kundenzahlen, Bewertungen oder Provisionssätze.

## Google-Richtlinien

- **Vertrauen (E-E-A-T):** Gründer mit echtem Foto, Adresse, Kontakt, echte Kundenarbeiten, Judge.me-Bewertungen sichtbar.
- **Strukturierte Daten:** Organization erweitern (Gründer, E-Mail, Gründungsjahr), `WebSite`, Produkt über
  `{{ product | structured_data }}` (vorher prüfen, ob `main-product` schon JSON-LD ausgibt, Doppelung vermeiden),
  `BreadcrumbList`, `FAQPage` auf der FAQ-Seite.
- **Tempo:** Ziel mobil LCP unter 2.5 s, CLS unter 0.1. Hero-Bild `fetchpriority="high"`, alle anderen `loading="lazy"`,
  überall `image_url` + `srcset` + `width`/`height`, Iconfont und `theme.min.css` entfernen, JS `defer`.
- **Auffindbarkeit:** genau eine H1 pro Seite, sprechende Titel/Beschreibungen (Suchbegriffe: JDM Merch Schweiz,
  JDM Hoodie, Auto auf T-Shirt, Custom Car Merch, Winterthur; DACH-Versand im Text), Alt-Texte, interne Links
  Galerie ↔ Custom ↔ Produkte. URLs bleiben unverändert.

## Phasen (nach jeder Phase: Upload, Screenshots, Commit)

0. Kopie anlegen, Dateien nach `theme/` holen, Baseline committen.
1. Designsystem: `nn.css`, `nn.js`, Snippets, `theme.liquid`, Header, Footer, Ticker, Warenkorb.
2. Startseite inkl. `nn-prozess`, `nn-galerie`, `nn-ueber-uns`. Danach Design-Kritik und Korrekturrunde.
3. Produkt, Kollektion, Suche.
4. Custom-Seite und Galerie-Template.
5. Story, FAQ, Kontakt, Partner, Oberteile, Sitemap, Widerruf, 404.
6. SEO-Durchgang, Barrierefreiheit, Tempo; `theme.min.css` und Iconfont entfernen; Abschlussprüfung.

## Prüfung

- Playwright (Chromium ist vorinstalliert) gegen die Vorschau-URL, 1440 px und 390 px, je Template:
  Screenshot, keine Konsolenfehler, kein horizontales Scrollen, Motion läuft, `prefers-reduced-motion` schaltet sie ab.
- Ablauf testen: Variante wählen → in den Warenkorb → Warenkorb öffnet → Link zur Kasse stimmt (nicht bezahlen).
- JSON-LD jeder Seite mit einem kurzen Skript parsen; pro Seite genau eine H1; Titel ≤ 60, Beschreibung ≤ 160 Zeichen.
- Lighthouse mobil auf Startseite und Produktseite: Leistung ≥ 90, SEO 100, Barrierefreiheit ≥ 95.
- Live-Theme unverändert (Rolle MAIN, `updatedAt` wie in der Ausgangslage).
- Falls die Vorschau-URL ohne Admin-Login nicht lädt: Fabio öffnet die Vorschau im Shopify-Admin; die
  Screenshot-Prüfung entfällt dann und das wird im Abschlussbericht klar gesagt.

## Was Fabio liefert (in Shopify unter Inhalte → Dateien hochladen, dann im Theme-Editor zuweisen)

- 3–5 Fotos: Fabio am Zeichnen, Fabio mit der Celica, Arbeitsplatz
- 1 Serie für die Scroll-Story: Kundenfoto des Autos, Bleistiftskizze, kolorierte Zeichnung, fertiges Shirt
- 6–20 Kundenfotos für die Galerie (mit Einverständnis der Kunden), je mit Automodell
- Niko als freigestellte Datei (PNG oder SVG)

## Schritte für den Livegang (nicht Teil dieses Auftrags, nur mit Fabios Freigabe)

- Seite «Galerie» anlegen und Template `page.galerie` zuweisen, ins Menü aufnehmen
- Fotos zuweisen, Texte gegenlesen
- Theme veröffentlichen (macht Fabio selbst im Admin). Das Live-Theme heisst `nipponnitestheme/main` und ist
  vermutlich mit einem GitHub-Repo verknüpft; vor dem Veröffentlichen klären, ob die Dateien dorthin sollen.
