# Theme V2 «Skizzenbuch»: Livegang

Theme in Shopify: **Nippon Nites – V2 Skizzenbuch (Claude)** (unveröffentlicht, ID in `THEME_ID.txt`).
Vorschau: https://nipponnites.com/?preview_theme_id=191806767379

Das Live-Theme `nipponnitestheme/main` wurde nicht verändert.

## Vor dem Veröffentlichen (im Shopify-Admin)

1. **Fotos hochladen** (Inhalte → Dateien) und im Theme-Editor zuweisen:
   - Startseite → Hero: Foto 1 «Fabio beim Zeichnen» (aktuell Fabio + Celica)
   - Startseite/Custom → «Vom Foto zum Unikat»: 4 Bilder (Kundenauto, Skizze, kolorierte Zeichnung, fertiges Shirt)
   - Kunden-Galerie: Blöcke «Kundenarbeit» anlegen (Foto, Auto, optional Kunde/Ort, nur mit Einverständnis)
2. **Seite «Galerie»** anlegen (Onlineshop → Seiten), Vorlage `page.galerie` wählen, ins Menü aufnehmen.
   Danach auf der Startseite bei «Kunden-Galerie» den Button-Link auf `/pages/galerie` setzen.
3. Texte gegenlesen.
4. Klären, ob das Live-Theme mit GitHub verbunden ist (Name `nipponnitestheme/main` deutet darauf hin).
   Falls ja: Dateien aus `theme/` in jenes Repo übernehmen, statt die Kopie zu veröffentlichen.
5. Veröffentlichen: Onlineshop → Themes → «Veröffentlichen».

## Tempo

Das Theme selbst braucht kaum Rechenzeit. Der Grossteil der Ladezeit kommt von Trackern und Apps
(Google Tag Manager 3×, Facebook-Pixel, Judge.me, Conversion Bear). Wer schneller werden will,
räumt dort auf (z. B. doppelte Google-Tags zusammenlegen).
