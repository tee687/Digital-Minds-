import json
from http.server import BaseHTTPRequestHandler, HTTPServer

with open("transactions.json") as f:
    transactions = json.load(f)

class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            return None

    def get_id(self):
        parts = self.path.split("/")
        if len(parts) == 3 and parts[1] == "transactions":
            try:
                return int(parts[2])
            except ValueError:
                return "bad"
        return None

    def find(self, tx_id):
        for t in transactions:
            if t["id"] == tx_id:
                return t
        return None

    def do_GET(self):
        if self.path == "/transactions":
            self.send_json(200, transactions)
            return

        tx_id = self.get_id()
        if tx_id is None:
            self.send_json(404, {"error": "Not found"})
        elif tx_id == "bad":
            self.send_json(400, {"error": "ID must be a number"})
        else:
            t = self.find(tx_id)
            if t:
                self.send_json(200, t)
            else:
                self.send_json(404, {"error": "Transaction not found"})

    def do_POST(self):
        if self.path != "/transactions":
            self.send_json(404, {"error": "Not found"})
            return

        data = self.read_body()
        if not isinstance(data, dict):
            self.send_json(400, {"error": "Invalid JSON body"})
            return

        new_id = max((t["id"] for t in transactions), default=0) + 1
        data["id"] = new_id
        transactions.append(data)
        self.send_json(201, data)

    def do_PUT(self):
        tx_id = self.get_id()
        if tx_id is None:
            self.send_json(404, {"error": "Not found"})
            return
        if tx_id == "bad":
            self.send_json(400, {"error": "ID must be a number"})
            return

        t = self.find(tx_id)
        if not t:
            self.send_json(404, {"error": "Transaction not found"})
            return

        data = self.read_body()
        if not isinstance(data, dict):
            self.send_json(400, {"error": "Invalid JSON body"})
            return

        data.pop("id", None)   # the id cannot be changed
        t.update(data)
        self.send_json(200, t)

    def do_DELETE(self):
        tx_id = self.get_id()
        if tx_id is None:
            self.send_json(404, {"error": "Not found"})
            return
        if tx_id == "bad":
            self.send_json(400, {"error": "ID must be a number"})
            return

        t = self.find(tx_id)
        if not t:
            self.send_json(404, {"error": "Transaction not found"})
            return

        transactions.remove(t)
        self.send_json(200, {"message": "Deleted"})

print("Server running on http://localhost:8000")
HTTPServer(("localhost", 8000), Handler).serve_forever()