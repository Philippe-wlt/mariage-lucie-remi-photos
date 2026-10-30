"""Prépare les photos du site.

Usage : python3 outils/preparer_photos.py <dossier_source>

<dossier_source> contient un sous-dossier par rubrique :
  ceremonie/, vin-honneur/, soiree/

Pour chaque photo : redressement selon l'orientation, tri par heure de prise
de vue (EXIF), une version web (2000 px) et une miniature (700 px).
Écrit photos/<rubrique>/... et photos.json à la racine du site.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

RUBRIQUES = ["ceremonie", "vin-honneur", "soiree"]
EXT = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}
RACINE = Path(__file__).resolve().parent.parent

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


def heure_prise(img):
    exif = img.getexif()
    sous = exif.get_ifd(0x8769)
    for valeur in (sous.get(36867), sous.get(36868), exif.get(306)):
        if valeur:
            try:
                return datetime.strptime(str(valeur).strip()[:19], "%Y:%m:%d %H:%M:%S")
            except ValueError:
                pass
    return None


def main(source):
    source = Path(source)
    resultat, sans_heure = {}, []
    for rub in RUBRIQUES:
        dossier = source / rub
        fichiers = sorted(p for p in dossier.rglob("*") if p.suffix.lower() in EXT) if dossier.exists() else []
        infos = []
        for f in fichiers:
            with Image.open(f) as im:
                h = heure_prise(im)
            if h is None:
                sans_heure.append(f"{rub}/{f.name}")
            infos.append((h or datetime.max, f.name, f))
        infos.sort()
        sortie = RACINE / "photos" / rub
        sortie.mkdir(parents=True, exist_ok=True)
        liste = []
        for n, (_, _, f) in enumerate(infos, 1):
            with Image.open(f) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                web = im.copy(); web.thumbnail((2000, 2000))
                web.save(sortie / f"{n:03d}.jpg", quality=85, optimize=True, progressive=True)
                mini = im.copy(); mini.thumbnail((700, 700))
                mini.save(sortie / f"{n:03d}-mini.jpg", quality=78, optimize=True, progressive=True)
            liste.append({"web": f"photos/{rub}/{n:03d}.jpg", "mini": f"photos/{rub}/{n:03d}-mini.jpg",
                          "l": mini.width, "h": mini.height})
        resultat[rub] = liste
        print(f"{rub} : {len(liste)} photos")
    (RACINE / "photos.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=1), encoding="utf-8")
    if sans_heure:
        print("Sans heure de prise de vue (placées en fin de rubrique) :")
        for s in sans_heure:
            print("  " + s)


if __name__ == "__main__":
    main(sys.argv[1])
