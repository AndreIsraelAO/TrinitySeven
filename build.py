"""Builds the offline Trinity Seven APK from your own copy of the original 7.7 APK.
Usage: python build.py trinity-seven-7-7.apk [--apktool apktool.jar] [--signer uber-apk-signer.jar] [--sdk ANDROID_HOME] [--lang ja|en]
Needs on PATH: java (11-21) and javac. Output: out/Trinity7-offline.apk (debug-signed)."""
import argparse, glob, hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHA256 = "13b3b9f2e9e127fc13fd3b636b376fdd66bddd356cb44e996caa3470b3ca958c"
PROVIDER = '<provider android:authorities="com.avex.trinityseven.t7stub" android:exported="false" android:initOrder="1000" android:name="com.t7stub.StubProvider"/>'
WORK, OUT = os.path.join(HERE, "work"), os.path.join(HERE, "out")

def run(*cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def find(label, path, pattern):
    hits = sorted(glob.glob(pattern)) if not path else [path]
    if not hits or not os.path.exists(hits[-1]):
        sys.exit(f"{label} not found: pass it explicitly (see --help)")
    return os.path.abspath(hits[-1])

ap = argparse.ArgumentParser()
ap.add_argument("apk")
ap.add_argument("--apktool")
ap.add_argument("--signer")
ap.add_argument("--sdk", default=os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "")
ap.add_argument("--lang", choices=["ja", "en"], default="ja", help="game language: forced Locale (default: ja)")
ap.add_argument("--host", default="http://127.0.0.1:8080", help="server address, max 32 chars (default: embedded server)")
a = ap.parse_args()

if hashlib.sha256(open(a.apk, "rb").read()).hexdigest() != SHA256:
    sys.exit("This is not the original 7.7 APK (versionCode 88): SHA-256 does not match.")
apktool = find("apktool.jar", a.apktool, os.path.join(HERE, "apktool*.jar"))
signer = find("uber-apk-signer jar", a.signer, os.path.join(HERE, "uber-apk-signer*.jar"))
android_jar = find("android.jar (SDK platform 30)", None, os.path.join(a.sdk, "platforms", "android-30", "android.jar"))
d8 = find("d8 (SDK build-tools)", None, os.path.join(a.sdk, "build-tools", "*", "d8.bat" if os.name == "nt" else "d8"))

shutil.rmtree(WORK, ignore_errors=True)
dec, cls, dex = (os.path.join(WORK, n) for n in ("dec", "cls", "dex"))
os.makedirs(cls); os.makedirs(dex); os.makedirs(OUT, exist_ok=True)

run("java", "-jar", apktool, "d", "-s", "-o", dec, os.path.abspath(a.apk))
manifest = os.path.join(dec, "AndroidManifest.xml")
xml = open(manifest, encoding="utf-8").read()
assert "</application>" in xml, "unexpected manifest"
open(manifest, "w", encoding="utf-8").write(xml.replace("</application>", PROVIDER + "</application>", 1))

src = os.path.join(WORK, "src", "com", "t7stub")
os.makedirs(src)
java = open(os.path.join(HERE, "server", "embedded", "com", "t7stub", "StubProvider.java"), encoding="utf-8").read()
open(os.path.join(src, "StubProvider.java"), "w", encoding="utf-8").write(java.replace("Locale.JAPAN", "Locale.JAPAN" if a.lang == "ja" else "Locale.US"))
run("javac", "--release", "8", "-cp", android_jar, "-d", cls, os.path.join(src, "StubProvider.java"))
classes = [os.path.join(r, f) for r, _, fs in os.walk(cls) for f in fs if f.endswith(".class")]
run(d8, "--min-api", "21", "--lib", android_jar, "--output", dex, *classes)
assert not os.path.exists(os.path.join(dec, "classes4.dex")), "classes4.dex already exists in the original APK"
shutil.copy(os.path.join(dex, "classes.dex"), os.path.join(dec, "classes4.dex"))

unsigned, patched = os.path.join(WORK, "unsigned.apk"), os.path.join(WORK, "patched.apk")
run("java", "-jar", apktool, "b", "-f", "-o", unsigned, dec)
run(sys.executable, "-I", os.path.join(HERE, "server", "patch_apk.py"), unsigned, patched, a.host)
signed = os.path.join(WORK, "signed")
run("java", "-jar", signer, "-a", patched, "-o", signed)

final = os.path.join(OUT, "Trinity7-offline.apk" if a.lang == "ja" else f"Trinity7-offline-{a.lang}.apk")
shutil.copy(glob.glob(os.path.join(signed, "*.apk"))[0], final)
print("\nDone:", final)
