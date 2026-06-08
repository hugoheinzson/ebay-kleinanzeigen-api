#!/usr/bin/env python3
"""
Speichert eine Kleinanzeigen-Anzeige lokal als Markdown und in Notion.

Verwendung:
    python add_listing.py <url>
    python add_listing.py <url> --only-local   # ohne Notion
    python add_listing.py <url> --only-notion  # ohne lokale Dateien

Umgebungsvariablen:
    NOTION_TOKEN        Notion Integration Token
    NOTION_DATABASE_ID  ID der Wohnungssuche-Datenbank
    LISTINGS_DIR        Zielordner für lokale Dateien (Standard: ./listings)
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        sys.exit(1)

    url = args[0]
    only_local = "--only-local" in args
    only_notion = "--only-notion" in args

    print(f"Lade Anzeige: {url}")

    from immo_helper.scraper import scrape_listing

    listing = await scrape_listing(url)
    print(f"  Titel:  {listing['title']}")
    print(f"  Preis:  {listing['price']['raw']}")
    print(f"  Ort:    {listing['location']['full']}")
    print(f"  Bilder: {len(listing['images'])}")

    if not only_notion:
        import os
        from immo_helper.markdown_exporter import export

        output_dir = Path(os.getenv("LISTINGS_DIR", "listings"))
        md_path = export(listing, output_dir)
        print(f"\nMarkdown gespeichert: {md_path}")

    if not only_local:
        import os
        if not os.getenv("NOTION_TOKEN"):
            print("\n[Info] NOTION_TOKEN nicht gesetzt – Notion-Sync übersprungen.")
        elif not os.getenv("NOTION_DATABASE_ID"):
            print("\n[Info] NOTION_DATABASE_ID nicht gesetzt – Notion-Sync übersprungen.")
        else:
            from immo_helper.notion_sync import add_listing

            print("\nSynce nach Notion …")
            notion_url = await add_listing(listing)
            print(f"Notion-Seite: {notion_url}")

    print("\nFertig.")


if __name__ == "__main__":
    asyncio.run(main())
