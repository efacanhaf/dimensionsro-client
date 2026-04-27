"""
Read en.grf — for every UI BMP it contains, extract that English version,
recolor (blue→gray pure desat), and overwrite the matching path in
C:/RO-dev/Skin/dimensionsro_dark/.

This makes English-text buttons stay English (not Korean) while still being
recolored to the dark theme.
"""
import os
import sys
import struct
import zlib
from PIL import Image

sys.path.insert(0, r"C:\RO\tools")
from grf_crypto import decrypt_grf_entry

GRF = r"C:\RO-dev\en.grf"
DST_ROOT = r"C:\RO-dev\Skin\dimensionsro_dark"

MAGIC_PINK = (255, 0, 255)


def shift(r, g, b):
    if (r, g, b) == MAGIC_PINK:
        return MAGIC_PINK
    if b > r and b > g:
        L = 0.299 * r + 0.587 * g + 0.114 * b
        base = max(0, min(255, int(L)))
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


def main():
    with open(GRF, "rb") as f:
        f.seek(30)
        fto, = struct.unpack("<I", f.read(4))
        f.seek(46 + fto)
        rs, _ = struct.unpack("<II", f.read(8))
        decomp = zlib.decompress(f.read(rs))

    i = 0
    candidates = []
    while i < len(decomp):
        end = decomp.find(b"\x00", i)
        if end == -1:
            break
        name = decomp[i:end]
        i = end + 1
        if i + 17 > len(decomp):
            break
        cs, csa, real, t, off = struct.unpack("<IIIBI", decomp[i:i + 17])
        i += 17
        nl = name.lower()
        KO_UI = b"\xc0\xaf\xc0\xfa\xc0\xce\xc5\xcd\xc6\xe4\xc0\xcc\xbd\xba"
        if nl.endswith(b".bmp") and (KO_UI in nl or b"userinterface" in nl):
            candidates.append((name, cs, csa, real, t, off))

    print(f"en.grf UI BMP entries: {len(candidates)}")

    overlaid = errors = skipped = 0
    with open(GRF, "rb") as f:
        for name, cs, csa, real, t, off in candidates:
            f.seek(46 + off)
            raw = f.read(csa if csa else cs)
            try:
                if t == 1:
                    body = zlib.decompress(raw)
                else:
                    dec = decrypt_grf_entry(raw, t, cs)
                    body = zlib.decompress(dec)
            except Exception:
                errors += 1
                continue
            try:
                rel = name.decode("cp949", errors="replace")
            except Exception:
                rel = name.decode("latin-1", errors="replace")
            ko = "유저인터페이스"
            rl = rel.lower()
            if ko in rel:
                idx = rel.find(ko) + len(ko) + 1
                sub = rel[idx:]
            elif "userinterface" in rl:
                idx = rl.find("userinterface")
                sub = rel[idx:]
            else:
                continue
            sub = sub.replace("\\", os.sep).replace("/", os.sep)
            dst = os.path.join(DST_ROOT, sub)
            # Decode the BMP body, recolor, save
            tmp_in = dst + ".__engrf_tmp"
            try:
                with open(tmp_in, "wb") as tf:
                    tf.write(body)
                img = Image.open(tmp_in)
                out = recolor(img)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                out.save(dst, "BMP")
                overlaid += 1
            except Exception:
                errors += 1
            finally:
                try:
                    os.remove(tmp_in)
                except Exception:
                    pass

    print(f"overlaid: {overlaid}")
    print(f"errors:   {errors}")


if __name__ == "__main__":
    main()
