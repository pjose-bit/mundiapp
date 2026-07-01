"""
servidor.py – Sirve el dashboard por WiFi para verlo desde el celular.
Uso: python servidor.py
"""
import http.server
import socketserver
import socket
import os
import webbrowser

PORT = 8080
BASE = os.path.dirname(os.path.abspath(__file__))

def ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.254.254.254", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

os.chdir(BASE)
ip = ip_local()
url = f"http://{ip}:{PORT}/reportes/"

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silenciar logs de cada request

print(f"""
  ╔══════════════════════════════════════════════════╗
  ║          SERVIDOR MUNDIAL 2026 ACTIVO            ║
  ╠══════════════════════════════════════════════════╣
  ║  PC:     http://localhost:{PORT}/reportes/        ║
  ║  WiFi:   {url:<41}║
  ╚══════════════════════════════════════════════════╝
  Escanea el QR del dashboard con el celular.
  Ctrl+C para detener.
""")

webbrowser.open(url)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
