package com.t7stub;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import java.io.*;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;

/** Starts the Trinity Seven backend stub on 127.0.0.1:8080 when the process starts (providers init before Unity). Mirrors stub_server.py (server/test_stub.py checks both). */
public class StubProvider extends ContentProvider implements android.app.Application.ActivityLifecycleCallbacks {
    @Override public void onActivityPreCreated(android.app.Activity a, android.os.Bundle b) { java.util.Locale.setDefault(java.util.Locale.JAPAN); }
    @Override public void onActivityCreated(android.app.Activity a, android.os.Bundle b) { java.util.Locale.setDefault(java.util.Locale.JAPAN); }
    @Override public void onActivityStarted(android.app.Activity a) {}
    @Override public void onActivityResumed(android.app.Activity a) {}
    @Override public void onActivityPaused(android.app.Activity a) {}
    @Override public void onActivityStopped(android.app.Activity a) {}
    @Override public void onActivitySaveInstanceState(android.app.Activity a, android.os.Bundle b) {}
    @Override public void onActivityDestroyed(android.app.Activity a) {}

    private static final String SHARE_TEXT = "トリニティセブン 夢幻図書館と第7の太陽";
    private static final String PAGE = "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Trinity Seven</title><p>Servidor privado: esta p&aacute;gina n&atilde;o existe mais.</p>";
    private static File saveDir;

    @Override public boolean onCreate() {
        // il2cpp takes CurrentCulture from Locale.getDefault(); under pt-BR (comma decimal) EnemyManager.UpdateHpBar's
        // Single.Parse throws, the enemy is never marked as existing and takes no damage (also blocks tutorial dialogs).
        // Android re-applies the configuration locale on activity launch, so set it again right before onCreate (Unity init).
        java.util.Locale.setDefault(java.util.Locale.JAPAN);
        ((android.app.Application) getContext().getApplicationContext()).registerActivityLifecycleCallbacks(this);
        // Backups live next to the game's own es2/ saves (removed on uninstall: copy them out to migrate devices).
        saveDir = getContext().getExternalFilesDir("savedata");
        if (saveDir == null) saveDir = new File(getContext().getFilesDir(), "savedata");
        Thread t = new Thread(() -> {
            try (ServerSocket ss = new ServerSocket(8080, 50, InetAddress.getByName("127.0.0.1"))) {
                while (true) {
                    Socket s = ss.accept();
                    new Thread(() -> handle(s)).start();
                }
            } catch (IOException e) { /* port taken: another instance already serves */ }
        });
        t.setDaemon(true);
        t.start();
        return true;
    }

    private static void handle(Socket s) {
        try (Socket c = s) {
            c.setSoTimeout(10000);
            InputStream in = new BufferedInputStream(c.getInputStream());
            String[] req = line(in).split(" ");
            int len = 0;
            String ctype = "";
            for (String h; !(h = line(in)).isEmpty(); ) {
                String l = h.toLowerCase();
                if (l.startsWith("content-length:")) len = Integer.parseInt(h.substring(15).trim());
                else if (l.startsWith("content-type:")) ctype = h.substring(13).trim();
            }
            byte[] reqBody = new byte[len];
            for (int i = 0, n; i < len && (n = in.read(reqBody, i, len - i)) > 0; i += n) { }
            String path = req.length > 1 ? req[1].split("[?]")[0] : "";
            String type = "application/json", body = null;
            byte[] b = null;
            switch (path) {
                case "/time_index": type = "text/plain"; body = String.valueOf(System.currentTimeMillis() / 1000); break;
                case "/version_index": body = "{\"min_version\":\"0.0.0\",\"store_url\":\"\"}"; break;
                case "/closing_get": body = "{\"closed\":false}"; break;
                case "/user_generateId": body = "{\"user_id\":100000001}"; break;
                case "/text_index": type = "text/plain"; body = SHARE_TEXT; break;
                // GetJson<List<T>> / GetJsonArray: anything but a JSON array is dropped by the game.
                case "/ban_get": case "/news_get": case "/present_index": case "/saveRefresh_index":
                case "/assetBundle_index": case "/cropro_getCampaigns":
                case "/article_index": case "/bbs_get": case "/question_get": case "/question_getFromUserId": case "/question_search":
                case "/storyMaker_getFromUserId": case "/storyMaker_getLegendList": case "/storyMaker_getNewList":
                case "/storyMaker_getPopularList": case "/storyMaker_getRandomList": case "/ranking_getTournament": case "/ranking_getTeamRankList":
                    body = "[]"; break;
                case "/savedata/index.php": type = "application/octet-stream"; b = savedata(formFields(ctype, reqBody)); break;
                default:
                    if (path.startsWith("/release/") && !path.endsWith(".json")) { type = "text/html; charset=utf-8"; body = PAGE; }
                    else body = "{}";
            }
            if (b == null) b = body.getBytes("UTF-8");
            OutputStream out = c.getOutputStream();
            out.write(("HTTP/1.1 200 OK\r\nContent-Type: " + type + "\r\nContent-Length: " + b.length + "\r\nConnection: close\r\n\r\n").getBytes());
            out.write(b);
            out.flush();
        } catch (IOException | RuntimeException e) { /* drop malformed request */ }
    }

    /** EasySaveHelper backup protocol: empty body = success, "05" = not found (EasySaveHelper.GetError). */
    private static byte[] savedata(java.util.Map<String, byte[]> f) throws IOException {
        byte[] none = new byte[0];
        String key;
        try {
            java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-1");
            md.update(f.containsKey("tag") ? f.get("tag") : none);
            md.update((byte) 0);
            md.update(f.containsKey("password") ? f.get("password") : none);
            StringBuilder sb = new StringBuilder();
            for (byte x : md.digest()) sb.append(String.format("%02x", x));
            key = sb.toString();
        } catch (java.security.NoSuchAlgorithmException e) { throw new IOException(e); }
        File file = new File(saveDir, key);
        String mode = f.containsKey("mode") ? new String(f.get("mode"), "UTF-8") : "";
        byte[] data = f.get("data");
        if (mode.equals("upload") && data != null && data.length > 0) {
            saveDir.mkdirs();
            try (FileOutputStream o = new FileOutputStream(file)) { o.write(data); }
            return none;
        }
        if (!file.exists()) return "05".getBytes();
        if (mode.equals("download")) {
            byte[] r = new byte[(int) file.length()];
            try (DataInputStream i = new DataInputStream(new FileInputStream(file))) { i.readFully(r); }
            return r;
        }
        if (mode.equals("delete")) { file.delete(); return none; }
        return "04".getBytes();  // unknown mode -> RESULT.UNKNOWN
    }

    /** WWWForm posts urlencoded fields, or multipart when it carries binary data (backup upload). */
    private static java.util.Map<String, byte[]> formFields(String ctype, byte[] body) throws IOException {
        java.util.Map<String, byte[]> m = new java.util.HashMap<>();
        int bi = ctype.indexOf("boundary=");
        if (bi < 0) {
            for (String kv : new String(body, "UTF-8").split("&")) {
                int e = kv.indexOf('=');
                if (e > 0) m.put(java.net.URLDecoder.decode(kv.substring(0, e), "UTF-8"), java.net.URLDecoder.decode(kv.substring(e + 1), "UTF-8").getBytes("UTF-8"));
            }
            return m;
        }
        byte[] delim = ("--" + ctype.substring(bi + 9).split(";")[0].replace("\"", "").trim()).getBytes("ISO-8859-1");
        byte[] crlf2 = "\r\n\r\n".getBytes("ISO-8859-1");
        java.util.regex.Pattern name = java.util.regex.Pattern.compile("name=\"([^\"]*)\"");
        for (int p = indexOf(body, delim, 0); p >= 0; ) {
            int start = p + delim.length + 2;                   // skip delimiter + CRLF
            int next = indexOf(body, delim, start);
            int hEnd = indexOf(body, crlf2, start);
            if (next < 0 || hEnd < 0 || hEnd > next) break;
            java.util.regex.Matcher nm = name.matcher(new String(body, start, hEnd - start, "ISO-8859-1"));
            if (nm.find()) m.put(nm.group(1), java.util.Arrays.copyOfRange(body, hEnd + 4, next - 2));  // part ends with CRLF
            p = next;
        }
        return m;
    }

    private static int indexOf(byte[] a, byte[] t, int from) {
        outer:
        for (int i = from; i <= a.length - t.length; i++) {
            for (int j = 0; j < t.length; j++) if (a[i + j] != t[j]) continue outer;
            return i;
        }
        return -1;
    }

    private static String line(InputStream in) throws IOException {
        StringBuilder sb = new StringBuilder();
        for (int c; (c = in.read()) >= 0 && c != '\n'; ) if (c != '\r') sb.append((char) c);
        return sb.toString();
    }

    @Override public Cursor query(Uri u, String[] p, String s, String[] a, String o) { return null; }
    @Override public String getType(Uri u) { return null; }
    @Override public Uri insert(Uri u, ContentValues v) { return null; }
    @Override public int delete(Uri u, String s, String[] a) { return 0; }
    @Override public int update(Uri u, ContentValues v, String s, String[] a) { return 0; }
}
