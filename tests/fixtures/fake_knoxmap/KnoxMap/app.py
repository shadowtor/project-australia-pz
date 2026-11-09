"""Fake KnoxMap server: stdlib only, writes tiny deterministic outputs under ./output/<map>/ next to this file."""
import http.server
import json
import os
import pathlib

BASE = pathlib.Path(__file__).resolve().parent


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, d):
        b = json.dumps(d).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        self._send({"ok": True})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/api/generate":
            n = body["mapName"]
            d = BASE / "output" / n
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{n}.bmp").write_bytes(b"BM-" + n.encode())
            (d / f"{n}_veg.bmp").write_bytes(b"BMV-" + n.encode())
            (d / f"{n}.pzw").write_text(f"<world name='{n}'/>", encoding="utf-8")
            (d / "env.json").write_text(json.dumps({k: os.environ.get(k) for k in (
                "KNOXMAP_PBF_FILE", "KNOXMAP_OSM_SOURCE", "KNOXMAP_NO_DISCORD", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")}))
            (d / "request.json").write_text(json.dumps(body))
            if os.environ.get("FAKE_NETWORK"):
                print("Overpass request failed", flush=True)
            self._send({"mapName": n})
        else:
            self._send({"standalone": True})


class _App:
    def run(self, host, port, debug):
        http.server.HTTPServer((host, port), H).serve_forever()


app = _App()
