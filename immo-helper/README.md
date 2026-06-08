# Immo-helper

Speichert Kleinanzeigen-Immobilienanzeigen als Markdown-Dateien und synchronisiert sie in eine Notion-Datenbank.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# .env ausfüllen (NOTION_TOKEN + NOTION_DATABASE_ID)
```

### Notion einrichten

1. Unter https://www.notion.so/my-integrations eine neue Integration erstellen
2. `NOTION_TOKEN` aus der Integration kopieren
3. Die **Wohnungssuche**-Datenbank in Notion öffnen → **...** → **Connections** → Integration hinzufügen
4. `NOTION_DATABASE_ID` aus der Datenbank-URL kopieren

## Verwendung

```bash
# Anzeige erfassen (lokal + Notion)
python add_listing.py https://www.kleinanzeigen.de/s-anzeige/...

# Nur lokal speichern
python add_listing.py <url> --only-local

# Nur Notion (keine Bilder downloaden)
python add_listing.py <url> --only-notion
```

## Ergebnis

**Lokal** (`listings/<id>_<titel>/`):
```
listing.md      ← alle Daten + Bewertungsfelder
images/
  01.jpg
  02.jpg
  ...
```

**Notion**: Datenbankzeile mit Status (`Neu` / `Interessant` / `Vielleicht` / `Nein`), Preis, Ort, Zimmer, Fläche + alle Bilder eingebettet.
