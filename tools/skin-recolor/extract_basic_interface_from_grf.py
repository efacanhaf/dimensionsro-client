"""
Extract all basic_interface\\*.bmp entries from data.grf (the kRO 'basic' default
skin baked into the GRF) into a flat folder for recoloring.
"""
import os
import sys
import struct
import zlib

sys.path.insert(0, r"C:\RO\tools")
from grf_crypto import decrypt_grf_entry

GRF = r"C:\RO-prod\data.grf"
OUT = r"C:\RO-dev\.work-basic-skin-extract"

os.makedirs(OUT, exist_ok=True)

with open(GRF, "rb") as f:
    f.seek(30)
    file_table_offset, = struct.unpack("<I", f.read(4))
    f.seek(46 + file_table_offset)
    raw_size, real_size = struct.unpack("<II", f.read(8))
    decomp = zlib.decompress(f.read(raw_size))

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
    # cp949 dir name for "유저인터페이스" (User Interface)
    KO_UI = b"\xc0\xaf\xc0\xfa\xc0\xce\xc5\xcd\xc6\xe4\xc0\xcc\xbd\xba"
    if nl.endswith(b".bmp") and (KO_UI in nl or b"userinterface" in nl):
        candidates.append((name, cs, csa, real, t, off))

print(f"basic_interface BMP entries: {len(candidates)}")

extracted = 0
errors = 0
with open(GRF, "rb") as f:
    for name, cs, csa, real, t, off in candidates:
        f.seek(46 + off)
        raw = f.read(csa if csa else cs)
        try:
            if t == 1:
                # plain zlib
                body = zlib.decompress(raw)
            else:
                dec = decrypt_grf_entry(raw, t, cs)
                body = zlib.decompress(dec)
        except Exception as e:
            errors += 1
            continue
        # build flat name (preserve subdir if any)
        try:
            rel = name.decode("cp949", errors="replace")
        except Exception:
            rel = name.decode("latin-1", errors="replace")
        # rel = 'data\texture\<UI-dir>\<sub>\foo.bmp' — strip prefix down to the UI subdir
        rl = rel.lower()
        # find marker = either the cp949 ko UI dir or 'userinterface'
        ko = "유저인터페이스"
        if ko in rel:
            idx = rel.find(ko) + len(ko) + 1  # +1 for path sep
            sub = rel[idx:]
        elif "userinterface" in rl:
            idx = rl.find("userinterface")
            sub = rel[idx:]
        else:
            sub = rel
        sub = sub.replace("\\", os.sep).replace("/", os.sep)
        out_path = os.path.join(OUT, sub)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as o:
            o.write(body)
        extracted += 1

print(f"extracted: {extracted}")
print(f"errors:    {errors}")
print(f"out: {OUT}")
