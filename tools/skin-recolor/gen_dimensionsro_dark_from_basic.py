"""
Recolor the kRO 'basic' default skin (extracted from data.grf basic_interface)
into the DimensionsRO dark theme.

Strategy:
  - Panel WHITES / NEUTRALS preserved verbatim — black text on top must stay readable.
  - Only pixels with a clear blue cast (B > R+10 AND B > G+10) get swapped to dark gray
    at a fixed darker scale.
  - Magic-pink (255,0,255) preserved for engine color-key cutouts.
"""
import os
import shutil
from PIL import Image

SRC_ROOT = r"C:\RO-dev\.work-basic-skin-extract"
DST_ROOT = r"C:\RO-dev\Skin\dimensionsro_dark"

MAGIC_PINK = (255, 0, 255)


def shift(r, g, b):
    if (r, g, b) == MAGIC_PINK:
        return MAGIC_PINK
    if b > r and b > g:
        # clear blue accent → gray at SAME luminance (pure desaturation, no darkening)
        L = 0.299 * r + 0.587 * g + 0.114 * b
        base = int(L)
        base = max(0, min(255, base))
        return (base, max(0, base - 2), max(0, base - 5))
    return (r, g, b)


def recolor(img):
    if img.mode == "P":
        pal = list(img.getpalette() or [])
        if len(pal) < 768:
            pal = pal + [0] * (768 - len(pal))
        new_pal = []
        for i in range(256):
            r, g, b = pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]
            nr, ng, nb = shift(r, g, b)
            new_pal.extend([nr, ng, nb])
        out = img.copy()
        out.putpalette(new_pal)
        return out
    out = img.convert("RGB")
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            px[x, y] = shift(r, g, b)
    return out


def walk():
    if os.path.exists(DST_ROOT):
        for entry in os.listdir(DST_ROOT):
            full = os.path.join(DST_ROOT, entry)
            if os.path.isdir(full):
                shutil.rmtree(full, ignore_errors=True)
            else:
                try:
                    os.remove(full)
                except Exception:
                    pass
    saved = scanned = 0
    errors = []
    for root, dirs, files in os.walk(SRC_ROOT):
        rel_dir = os.path.relpath(root, SRC_ROOT)
        for fn in files:
            if not fn.lower().endswith(".bmp"):
                continue
            scanned += 1
            src = os.path.join(root, fn)
            rel = os.path.normpath(os.path.join(rel_dir, fn) if rel_dir != "." else fn)
            dst = os.path.join(DST_ROOT, rel)
            try:
                img = Image.open(src)
                out = recolor(img)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                out.save(dst, "BMP")
                saved += 1
            except Exception as e:
                errors.append(f"{rel}: {e}")
    print(f"scanned: {scanned}")
    print(f"saved:   {saved}")
    print(f"errors:  {len(errors)}")
    for e in errors[:10]:
        print(f"  {e}")


if __name__ == "__main__":
    walk()
