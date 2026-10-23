"""Checks a running stub over HTTP: python test_stub.py http://127.0.0.1:8080
Also checks that stub_server.py and StubProvider.java list the same JSON-array routes."""
import json, os, re, sys, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stub_server

java = open(os.path.join(HERE, "embedded/com/t7stub/StubProvider.java"), encoding="utf-8").read()
java_lists = set(re.findall(r'case "(/[^"]+)":', java[java.index("anything but a JSON array"):java.index('body = "[]"')]))
assert java_lists == stub_server.LIST_ROUTES, ("list routes differ", java_lists ^ stub_server.LIST_ROUTES)

base = sys.argv[1].rstrip("/")

def call(path, data=None, ctype=None):
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": ctype} if ctype else {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read(), r.headers.get("Content-Type", "")

def multipart(fields):  # same shape as UnityEngine.WWWForm with AddBinaryData
    b = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n".encode() + v + b"\r\n"
    return out + f"--{b}--\r\n".encode(), "multipart/form-data; boundary=" + b

def form(**kw):
    return "&".join(f"{k}={v}" for k, v in kw.items()).encode(), "application/x-www-form-urlencoded"

for p in sorted(stub_server.LIST_ROUTES):
    assert json.loads(call(p + "?appid=tri")[0]) == [], p
assert call("/text_index")[0].decode() == stub_server.SHARE_TEXT
assert "text/html" in call("/release/help/index.html")[1]
assert json.loads(call("/release/android/asset_info.json")[0]) == {}
assert json.loads(call("/version_index")[0])["min_version"] == "0.0.0"

tag, pw = "100000001", uuid.uuid4().hex[:8]
save = bytes(range(256)) * 40 + b"\r\n--tail"            # binary, contains CRLF and dashes
assert call("/savedata/index.php", *form(tag=tag, password=pw, mode="download"))[0] == b"05"
assert call("/savedata/index.php", *multipart({"tag": tag.encode(), "password": pw.encode(), "mode": b"upload",
                                                "filename": b"__tmp_esbu__", "data": save}))[0] == b""
assert call("/savedata/index.php", *form(tag=tag, password=pw, mode="download"))[0] == save
assert call("/savedata/index.php", *form(tag=tag, password="wrong", mode="download"))[0] == b"05"
assert call("/savedata/index.php", *form(tag=tag, password=pw, mode="delete"))[0] == b""
assert call("/savedata/index.php", *form(tag=tag, password=pw, mode="download"))[0] == b"05"
print("ok", base)
