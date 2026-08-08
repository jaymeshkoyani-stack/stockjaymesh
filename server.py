import http.server
import socketserver
import json
import os
import time
from fetch_all_216_full import fetch_all_symbols_complete

PORT = 8080
DIRECTORY = os.path.dirname(__file__)

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/api/sync":
            self.handle_sync_request()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        if self.path == "/api/sync":
            self.handle_sync_request()
        else:
            super().do_GET()

    def handle_sync_request(self):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Received manual sync request from UI. Re-logging into iCharts...")
        try:
            count = fetch_all_symbols_complete()
            response_data = {
                "status": "success",
                "message": f"Successfully re-authenticated login and updated {count} symbols from iCharts!",
                "count": count,
                "timestamp": time.strftime('%H:%M:%S')
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        except Exception as e:
            err_msg = str(e)
            print(f"[!] Error during manual re-login sync: {err_msg}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": err_msg}).encode("utf-8"))

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardHTTPRequestHandler) as httpd:
        print(f"[*] iCharts Live Master Dashboard Server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
