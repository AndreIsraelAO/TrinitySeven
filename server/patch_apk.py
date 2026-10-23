"""Redirect the APK's hardcoded hosts to a local server by editing global-metadata.dat string literals in place.
Usage: python patch_apk.py in.apk out.apk http://192.168.1.10:8080
The output is UNSIGNED: sign it (apksigner) before installing."""
import importlib.util, os, struct, sys, zipfile

SRC = ["https://app-tri.poppin-games.com", "https://d3q92yhknzclgr.cloudfront.net", "https://d26dq7zel370l.cloudfront.net"]
META = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
LIB = "lib/arm64-v8a/libil2cpp.so"

def load_patch_lib():
    spec = importlib.util.spec_from_file_location("patch_lib", os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch_lib.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def patch(meta: bytearray, new: str) -> int:
    lit_off, lit_size, data_off, _ = struct.unpack_from("<4i", meta, 8)
    count = 0
    for i in range(lit_size // 8):
        length, idx = struct.unpack_from("<Ii", meta, lit_off + i * 8)
        s = bytes(meta[data_off + idx: data_off + idx + length])
        for old in SRC:
            if s.startswith(old.encode()):
                t = new.encode() + s[len(old):]
                assert len(t) <= length, "new host longer than original; use a shorter host"
                meta[data_off + idx: data_off + idx + len(t)] = t
                struct.pack_into("<I", meta, lit_off + i * 8, len(t))
                count += 1
                break
    return count

if __name__ == "__main__":
    src, dst, host = sys.argv[1:4]
    host = host.rstrip("/")
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w") as zo:
        for it in zi.infolist():
            if it.filename.startswith("META-INF/") and it.filename.endswith((".SF", ".RSA", ".DSA", ".EC", ".MF")):
                continue  # old signature is invalid after patching
            data = zi.read(it)
            if it.filename == META:
                b = bytearray(data)
                print("patched literals:", patch(b, host))
                data = bytes(b)
            elif it.filename == LIB:
                b = bytearray(data)
                load_patch_lib().patch(b)
                print("patched libil2cpp offline getters")
                data = bytes(b)
            zo.writestr(it, data, compress_type=it.compress_type)
