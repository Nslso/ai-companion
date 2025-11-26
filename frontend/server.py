import http.server
import socketserver
import os

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def end_headers(self):
        # Добавляем CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

PORT = 3000

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend server running at http://localhost:{PORT}")
    httpd.serve_forever()