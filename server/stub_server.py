"""Stub for the Trinity Seven backend. Shapes come from dump.cs (IL2CPP dump); unverified against a live server.
Run: python stub_server.py [port]. Every request is logged so unknown endpoints show up.
Keep the routes in sync with embedded/com/t7stub/StubProvider.java (test_stub.py checks it)."""
import email, hashlib, json, os, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# path -> (content-type, body). Bodies follow the C# classes read via NetworkHelper.GetJson<T>.
ROUTES = {
    "/time_index": ("text/plain", lambda q: str(int(time.time()))),                    # CheatManager: unixTimeString
    "/version_index": ("application/json", lambda q: {"min_version": "0.0.0", "store_url": ""}),  # VersionData
    "/closing_get": ("application/json", lambda q: {"closed": False}),                 # Close
    "/user_generateId": ("application/json", lambda q: {"user_id": 100000001}),        # GeneratedUser
    "/release/android/asset_info.json": ("application/json", lambda q: {}),            # Dictionary<string,int>
    "/text_index": ("text/plain", lambda q: SHARE_TEXT),                               # GetText: share dialog body
}
# GetJson<List<T>> / GetJsonArray: anything but a JSON array is dropped by the game, so these must answer [].
LIST_ROUTES = {
    "/ban_get", "/news_get", "/present_index", "/saveRefresh_index", "/assetBundle_index", "/cropro_getCampaigns",
    "/article_index", "/bbs_get", "/question_get", "/question_getFromUserId", "/question_search",
    "/storyMaker_getFromUserId", "/storyMaker_getLegendList", "/storyMaker_getNewList",
    "/storyMaker_getPopularList", "/storyMaker_getRandomList", "/ranking_getTournament", "/ranking_getTeamRankList",
}
SHARE_TEXT = "トリニティセブン 夢幻図書館と第7の太陽"
PAGE = "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Trinity Seven</title><p>Servidor privado: esta p&aacute;gina n&atilde;o existe mais.</p>"
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savedata")
DELAY = float(sys.argv[2]) if len(sys.argv) > 2 else 0  # seconds; experiment: emulate network latency

def form_fields(ctype, body):
    """WWWForm posts urlencoded fields, or multipart when it carries binary data (backup upload)."""
    if ctype.startswith("multipart/"):
        msg = email.message_from_bytes(b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + body)
        return {p.get_param("name", header="content-disposition"): p.get_payload(decode=True) for p in msg.get_payload()}
    return {k: v[0].encode() for k, v in parse_qs(body.decode("utf8", "replace")).items()}

def savedata(f):
    """EasySaveHelper backup protocol: empty body = success, "05" = not found (EasySaveHelper.GetError)."""
    key = hashlib.sha1(f.get("tag", b"") + b"\0" + f.get("password", b"")).hexdigest()
    path = os.path.join(SAVE_DIR, key)
    mode = f.get("mode", b"").decode()
    if mode == "upload" and f.get("data"):
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(path, "wb") as fh: fh.write(f["data"])
        return b""
    if not os.path.exists(path): return b"05"
    if mode == "download":
        with open(path, "rb") as fh: return fh.read()
    if mode == "delete":
        os.remove(path)
        return b""
    return b"04"  # unknown mode -> RESULT.UNKNOWN

def respond(method, path, ctype, body):
    """-> (content-type, bytes, known)."""
    if path == "/savedata/index.php" and method == "POST":
        return "application/octet-stream", savedata(form_fields(ctype, body)), True
    if path in LIST_ROUTES:
        return "application/json", b"[]", True
    if path in ROUTES:
        t, fn = ROUTES[path]
        out = fn(None)
        return t, (out if isinstance(out, str) else json.dumps(out)).encode(), True
    if path.startswith("/release/") and not path.endswith(".json"):  # help/terms/privacy/credit pages opened in a browser
        return "text/html; charset=utf-8", PAGE.encode(), True
    return "application/json", b"{}", False

class H(BaseHTTPRequestHandler):
    def _go(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        time.sleep(DELAY)
        ctype, data, known = respond(self.command, u.path, self.headers.get("Content-Type", ""), body)
        print(f"{self.command} {self.path} {body[:200]!r} -> {'OK' if known else 'FALLBACK {}'}", flush=True)
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    do_GET = do_POST = _go

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
