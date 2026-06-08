import asyncio
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


def export(listing: Dict[str, Any], output_dir: Path) -> Path:
    """Save listing as Markdown with downloaded images. Returns path to .md file."""
    slug = _slug(listing["title"])
    listing_dir = output_dir / f"{listing['id']}_{slug}"
    images_dir = listing_dir / "images"
    listing_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(exist_ok=True)

    local_images = _download_images(listing["images"], images_dir)
    md = _render(listing, local_images)

    md_path = listing_dir / "listing.md"
    md_path.write_text(md, encoding="utf-8")
    return md_path


def _download_images(urls: List[str], dest: Path) -> List[Path]:
    local = []
    for i, url in enumerate(urls, 1):
        ext = _image_ext(url)
        filename = f"{i:02d}{ext}"
        path = dest / filename
        if not path.exists():
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    path.write_bytes(resp.read())
            except Exception as e:
                print(f"  [Warnung] Bild {i} konnte nicht geladen werden: {e}")
                continue
        local.append(path)
    return local


def _render(listing: Dict[str, Any], local_images: List[Path]) -> str:
    price = listing["price"]
    price_str = f"{int(price['amount']):,} {price['currency']}".replace(",", ".") if price["amount"] else price["raw"]
    if price["negotiable"]:
        price_str += " VB"

    loc = listing["location"]
    location_str = f"{loc['zip']} {loc['city']}".strip() or loc["full"]

    lines = [
        f"# {listing['title']}",
        "",
        f"**Status**: Neu",
        f"**Preis**: {price_str}",
        f"**Ort**: {location_str}",
    ]

    # Details (Zimmer, Fläche etc. come from structured details)
    if listing.get("details"):
        for key, val in listing["details"].items():
            lines.append(f"**{key}**: {val}")

    lines += [
        f"**Eingestellt**: {listing['created_at']}",
        f"**Anzeigen-ID**: {listing['id']}",
        f"**URL**: {listing['url']}",
        "",
        "---",
        "",
        "## Beschreibung",
        "",
        listing.get("description") or "_Keine Beschreibung_",
        "",
        "---",
        "",
        "## Bilder",
        "",
    ]

    for img_path in local_images:
        rel = f"images/{img_path.name}"
        lines.append(f"![{img_path.stem}]({rel})")
        lines.append("")

    if not local_images and listing.get("images"):
        # Fallback: link to original URLs
        for url in listing["images"]:
            lines.append(f"![]({url})")
            lines.append("")

    lines += [
        "---",
        "",
        "## Meine Bewertung",
        "",
        "**Entscheidung**: <!-- Interessant / Vielleicht / Nein -->",
        "",
        "**Notizen**:",
        "",
        "",
    ]

    return "\n".join(lines)


def _slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[äöüß]", lambda m: {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}[m.group()], text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text[:60].strip("-")


def _image_ext(url: str) -> str:
    for ext in (".webp", ".jpg", ".jpeg", ".png", ".gif"):
        if ext in url.lower():
            return ext
    return ".jpg"
