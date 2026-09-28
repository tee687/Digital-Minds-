import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

AUTH = "Basic " + base64.b64encode(b"admin:password123").decode()

# In-memory dictionary for fast O(1) CRUD operations
db = {
    "1": {
        "id": "1",
        "type": "payment",
        "amount": 5000.0,
        "sender": "Alice",
        "receiver": "SIMBA SUPERMARKET",
        "timestamp": "2026-09-28 10:15:00",
    },
    "2": {
        "id": "2",
        "type": "transfer",
        "amount": 12000.0,
        "sender": "Tendai",
        "receiver": "Charlie",
        "timestamp": "2026-09-28 11:30:00",
    },
}


class MoMoHandler(BaseHTTPRequestHandler):

    def send_data(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def check_auth(self):
        if self.headers.get("Authorization") != AUTH:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}')
            return False
        return True

    def get_id(self):
        parts = self.path.strip("/").split("/")
        return parts[1] if len(parts) == 2 and parts[0] == "transactions" else None

    def get_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode()) if length else {}

    def do_GET(self):
        if not self.check_auth():
            return
        tid = self.get_id()
        if self.path == "/transactions":
            self.send_data(200, list(db.values()))
        elif tid and tid in db:
            self.send_data(200, db[tid])
        else:
            self.send_data(404, {"error": "Not Found"})

    def do_POST(self):
        if not self.check_auth():
            return
        if self.path == "/transactions":
            item = self.get_body()
            if "id" in item:
                db[item["id"]] = item
                self.send_data(201, item)
            else:
                self.send_data(400, {"error": "Missing id"})
        else:
            self.send_data(404, {"error": "Not Found"})

    def do_PUT(self):
        if not self.check_auth():
            return
        tid = self.get_id()
        if tid and tid in db:
            db[tid].update(self.get_body())
            self.send_data(200, db[tid])
        else:
            self.send_data(404, {"error": "Not Found"})

    def do_DELETE(self):
        if not self.check_auth():
            return
        tid = self.get_id()
        if tid and tid in db:
            del db[tid]
            self.send_data(200, {"message": f"Deleted {tid}"})
        else:
            self.send_data(404, {"error": "Not Found"})


if __name__ == "__main__":
    print("Server running on http://localhost:8000")
    HTTPServer(("", 8000), MoMoHandler).serve_forever()