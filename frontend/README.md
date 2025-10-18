# Kleinanzeigen-API Frontend

Eine moderne Web-UI für die Kleinanzeigen-API. Bietet eine benutzerfreundliche Oberfläche zum Durchsuchen von Kleinanzeigen mit erweiterten Filteroptionen.

## Features

- 🔍 **Intelligente Suche** - Suche nach Produkten mit Suchbegriff
- 📍 **Standortbasiert** - Suche mit Standort und Umkreis
- 🏷️ **Kategorien** - Filtere nach verschiedenen Produktkategorien
- 💰 **Preisspanne** - Filtere Ergebnisse nach Min/Max Preis
- 📊 **Sortierung** - Sortiere nach Relevanz, Preis oder Datum
- 📱 **Responsive Design** - Funktioniert auf Desktop, Tablet und Mobile
- ⚡ **Schnell** - Built mit Next.js und React 18

## Installation

### Voraussetzungen

- Node.js 18+ oder höher
- npm oder yarn
- Laufende Kleinanzeigen-API auf `http://localhost:8000`

### Setup

1. **Navigiere zum Frontend-Verzeichnis:**

```bash
cd frontend
```

2. **Installiere Dependencies:**

```bash
npm install
# oder
yarn install
```

3. **Starte den Development Server:**

```bash
npm run dev
# oder
yarn dev
```

4. **Öffne die App im Browser:**

Navigiere zu [http://localhost:3000](http://localhost:3000)

## Verwendung

### Backend API starten

Bevor du die UI verwendest, stelle sicher, dass die Backend-API läuft:

```bash
# Im Root-Verzeichnis des Projekts
python serve.py
```

Die API sollte auf `http://localhost:8000` verfügbar sein.

### Suchparameter

Die UI unterstützt folgende Suchparameter:

- **Suchbegriff** - Was du suchst (z.B. "iPhone 14", "Fahrrad")
- **Standort** - Stadt oder PLZ für die Suche
- **Umkreis** - 10-200 km Radius um den Standort
- **Kategorie** - Produktkategorie (Auto, Elektronik, etc.)
- **Preisspanne** - Minimum und Maximum Preis
- **Sortierung** - Nach Relevanz, Preis oder Datum

### Beispiel-Suchen

1. **iPhone in München:**
   - Suchbegriff: "iPhone 14"
   - Standort: "München"
   - Umkreis: 50 km

2. **Fahrrad unter 300€:**
   - Suchbegriff: "Fahrrad"
   - Kategorie: "Auto, Rad & Boot"
   - Max. Preis: 300

3. **Neueste Möbel:**
   - Kategorie: "Haus & Garten"
   - Sortierung: "Neueste zuerst"

## Projekt-Struktur

```
frontend/
├── app/
│   ├── components/
│   │   ├── SearchForm.tsx      # Suchformular mit Filtern
│   │   └── SearchResults.tsx   # Ergebnisdarstellung
│   ├── globals.css             # Globale Styles
│   ├── layout.tsx              # Root Layout
│   ├── page.tsx                # Hauptseite
│   └── types.ts                # TypeScript Typen
├── next.config.js              # Next.js Konfiguration
├── package.json                # Dependencies
├── postcss.config.js           # PostCSS Config
├── tailwind.config.js          # Tailwind Config
└── tsconfig.json               # TypeScript Config
```

## Technologie-Stack

- **Framework:** Next.js 14 (App Router)
- **UI Library:** React 18
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **HTTP Client:** Axios
- **Language:** TypeScript

## API-Endpunkte

Die UI kommuniziert mit folgenden Backend-Endpunkten:

- `GET /inserate` - Suche nach Kleinanzeigen
  - Query-Parameter: `q`, `ort`, `radius`, `kategorie`, `preis_min`, `preis_max`, `sortierung`

## Customization

### API-URL ändern

Bearbeite `next.config.js` um die Backend-URL zu ändern:

```javascript
async rewrites() {
  return [
    {
      source: '/api/backend/:path*',
      destination: 'http://your-api-url:8000/:path*',
    },
  ]
}
```

### Kategorien anpassen

Bearbeite `app/components/SearchForm.tsx` um Kategorien hinzuzufügen oder zu ändern:

```typescript
const categories = [
  { value: 'ID', label: 'Kategoriename' },
  // ...
]
```

### Styling anpassen

Die App verwendet Tailwind CSS. Passe `tailwind.config.js` an, um das Design zu ändern.

## Production Build

Für Production:

```bash
npm run build
npm start
```

## Docker Support

Die UI kann auch mit Docker deployed werden. Erstelle ein `Dockerfile` im Frontend-Verzeichnis:

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

Build und run:

```bash
docker build -t kleinanzeigen-ui .
docker run -p 3000:3000 kleinanzeigen-ui
```

## Troubleshooting

### API-Verbindungsfehler

- Stelle sicher, dass die Backend-API auf Port 8000 läuft
- Überprüfe die CORS-Einstellungen in der API
- Prüfe die Browser-Console auf Fehler

### Keine Ergebnisse

- Überprüfe die Suchparameter
- Teste den API-Endpunkt direkt im Browser: `http://localhost:8000/inserate?q=test`
- Überprüfe die API-Logs

## Lizenz

Siehe LICENSE-Datei im Root-Verzeichnis des Projekts.

## Support

Bei Fragen oder Problemen, erstelle ein Issue im GitHub Repository.
