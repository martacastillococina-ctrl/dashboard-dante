#!/usr/bin/env python3
"""
server.py - Servidor HTTP liviano para el Dashboard de Dante.
Corre en puerto 5050, soporta API REST y sirve la interfaz web.
"""
import json
import mimetypes
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

# Encoding seguro en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

sys.path.insert(0, str(BASE_DIR))
import core

PORT = 5050

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def _responder_json(self, data, status=200):
        cuerpo = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _responder_texto(self, texto, status=200, mime="text/plain; charset=utf-8"):
        cuerpo = texto.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/items":
            items = core.obtener_db()
            return self._responder_json(items)

        if path == "/api/inbox-md":
            items = core.obtener_db()
            core.generar_markdowns(items)
            contenido = ""
            if core.INBOX_MD_PATH.exists():
                with open(core.INBOX_MD_PATH, "r", encoding="utf-8") as f:
                    contenido = f.read()
            return self._responder_texto(contenido)

        if path == "/api/stats":
            items = core.obtener_db()
            stats = {
                "total": len(items),
                "pendientes": len([i for i in items if i.get("status") in ("pendiente", "en_proceso")]),
                "directivas": len([i for i in items if i.get("type") == "directiva_claude" and i.get("status") != "listo"]),
                "referencias": len([i for i in items if i.get("type") == "referencia"]),
                "ideas": len([i for i in items if i.get("type") == "idea"]),
                "completados": len([i for i in items if i.get("status") == "listo"])
            }
            return self._responder_json(stats)

        # Servir index.html para raíz
        if path in ("/", ""):
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo_bytes = self.rfile.read(longitud)
        
        try:
            datos = json.loads(cuerpo_bytes.decode("utf-8")) if cuerpo_bytes else {}
        except Exception as e:
            return self._responder_json({"error": "JSON malformado", "detalle": str(e)}, 400)

        if path == "/api/items":
            if not datos.get("title"):
                return self._responder_json({"error": "El título es obligatorio"}, 400)
            nuevo = core.agregar_item(datos)
            return self._responder_json(nuevo, 201)

        if path.startswith("/api/status/"):
            item_id = path.replace("/api/status/", "").strip()
            nuevo_estado = datos.get("status", "pendiente")
            actualizado = core.actualizar_item(item_id, {"status": nuevo_estado})
            if actualizado:
                return self._responder_json(actualizado)
            return self._responder_json({"error": "Item no encontrado"}, 404)

        if path == "/api/sync":
            items = core.obtener_db()
            core.generar_markdowns(items)
            return self._responder_json({"success": True, "items_count": len(items)})

        return self._responder_json({"error": "Ruta POST no encontrada"}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/items/"):
            item_id = path.replace("/api/items/", "").strip()
            longitud = int(self.headers.get("Content-Length", 0))
            cuerpo_bytes = self.rfile.read(longitud)
            try:
                datos = json.loads(cuerpo_bytes.decode("utf-8")) if cuerpo_bytes else {}
            except Exception as e:
                return self._responder_json({"error": "JSON malformado", "detalle": str(e)}, 400)

            actualizado = core.actualizar_item(item_id, datos)
            if actualizado:
                return self._responder_json(actualizado)
            return self._responder_json({"error": "Item no encontrado"}, 404)

        return self._responder_json({"error": "Ruta PUT no encontrada"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/items/"):
            item_id = path.replace("/api/items/", "").strip()
            exito = core.eliminar_item(item_id)
            if exito:
                return self._responder_json({"success": True, "id": item_id})
            return self._responder_json({"error": "Item no encontrado"}, 404)

        return self._responder_json({"error": "Ruta DELETE no encontrada"}, 404)

def main():
    print(f"Iniciando Dashboard de Dante en http://localhost:{PORT} ...")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"Servidor listo en http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        server.server_close()

if __name__ == "__main__":
    main()
