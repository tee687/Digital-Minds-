import json
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer

with open("transactions.json") as f:
    transactions = json.load(f)

USERNAME = "admin"
PASSWORD = "password123"


class Handler(BaseHTTPRequestHandler):

    def check_auth(self):
        auth_header = self.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Basic "):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
            self.end_headers()
            return False

        try:
            encoded_credentials = auth_header.split(" ", 1)[1]
            decoded_credentials = base64.b64decode(
                encoded_credentials
            ).decode("utf-8")

            username, password = decoded_credentials.split(":", 1)

            if username == USERNAME and password == PASSWORD:
                return True

        except (ValueError, UnicodeDecodeError, base64.binascii.Error):
            pass

        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
        self.end_headers()
        return False

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
        if not self.check_auth():
            return

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
        if not self.check_auth():
            return

        if self.path != "/transactions":
            self.send_json(404, {"error": "Not found"})
            return

        data = self.read_body()

        if not isinstance(data, dict):
            self.send_json(400, {"error": "Invalid JSON body"})
            return

        new_id = max(
            (t["id"] for t in transactions),
            default=0
        ) + 1

        data["id"] = new_id
        transactions.append(data)

        self.send_json(201, data)

    def do_PUT(self):
        if not self.check_auth():
            return

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

        data.pop("id", None)
        t.update(data)

        self.send_json(200, t)

    def do_DELETE(self):
        if not self.check_auth():
            return

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

import json
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "transactions.json"

USERNAME = "admin"
PASSWORD = "password123"


def load_transactions():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


transactions = load_transactions()


def save_transactions():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(transactions, file, indent=2, ensure_ascii=False)


class TransactionHandler(BaseHTTPRequestHandler):

    def authenticate(self):
        auth_header = self.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Basic "):
            return False

        try:
            encoded_credentials = auth_header.split(" ")[1]
            credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = credentials.split(":", 1)

            return username == USERNAME and password == PASSWORD

        except Exception:
            return False

    def require_authentication(self):
        if not self.authenticate():
            self.send_response(401)
            self.send_header(
                "WWW-Authenticate",
                'Basic realm="MoMo API"'
            )
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(
                json.dumps({
                    "error": "Unauthorized"
                }).encode("utf-8")
            )

            return False

        return True

    def send_json(self, status_code, data):
        response = json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()

        self.wfile.write(response)

    def get_transaction_id(self):
        parts = self.path.strip("/").split("/")

        if len(parts) == 2 and parts[0] == "transactions":
            try:
                return int(parts[1])
            except ValueError:
                return None

        return None

    def read_request_body(self):
        try:
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(content_length)

            return json.loads(body.decode("utf-8"))

        except Exception:
            return None

    def do_GET(self):

        if not self.require_authentication():
            return

        if self.path == "/transactions":
            self.send_json(200, transactions)
            return

        transaction_id = self.get_transaction_id()

        if transaction_id is not None:

            for transaction in transactions:

                if transaction["id"] == transaction_id:
                    self.send_json(200, transaction)
                    return

            self.send_json(
                404,
                {"error": "Transaction not found"}
            )
            return

        self.send_json(
            404,
            {"error": "Endpoint not found"}
        )

    def do_POST(self):

        if not self.require_authentication():
            return

        if self.path != "/transactions":
            self.send_json(
                404,
                {"error": "Endpoint not found"}
            )
            return

        data = self.read_request_body()

        if not data:
            self.send_json(
                400,
                {"error": "Invalid JSON"}
            )
            return

        required_fields = [
            "type",
            "amount",
            "sender",
            "receiver",
            "timestamp"
        ]

        for field in required_fields:

            if field not in data:
                self.send_json(
                    400,
                    {"error": f"Missing field: {field}"}
                )
                return

        new_id = max(
            transaction["id"]
            for transaction in transactions
        ) + 1

        new_transaction = {
            "id": new_id,
            "type": data["type"],
            "amount": data["amount"],
            "sender": data["sender"],
            "receiver": data["receiver"],
            "timestamp": data["timestamp"]
        }

        transactions.append(new_transaction)

        save_transactions()

        self.send_json(
            201,
            new_transaction
        )

    def do_PUT(self):

        if not self.require_authentication():
            return

        transaction_id = self.get_transaction_id()

        if transaction_id is None:
            self.send_json(
                400,
                {"error": "Invalid transaction ID"}
            )
            return

        data = self.read_request_body()

        if not data:
            self.send_json(
                400,
                {"error": "Invalid JSON"}
            )
            return

        for index, transaction in enumerate(transactions):

            if transaction["id"] == transaction_id:

                updated_transaction = {
                    "id": transaction_id,
                    "type": data.get(
                        "type",
                        transaction["type"]
                    ),
                    "amount": data.get(
                        "amount",
                        transaction["amount"]
                    ),
                    "sender": data.get(
                        "sender",
                        transaction["sender"]
                    ),
                    "receiver": data.get(
                        "receiver",
                        transaction["receiver"]
                    ),
                    "timestamp": data.get(
                        "timestamp",
                        transaction["timestamp"]
                    )
                }

                transactions[index] = updated_transaction

                save_transactions()

                self.send_json(
                    200,
                    updated_transaction
                )
                return

        self.send_json(
            404,
            {"error": "Transaction not found"}
        )

    def do_DELETE(self):

        if not self.require_authentication():
            return

        transaction_id = self.get_transaction_id()

        if transaction_id is None:
            self.send_json(
                400,
                {"error": "Invalid transaction ID"}
            )
            return

        for index, transaction in enumerate(transactions):

            if transaction["id"] == transaction_id:

                deleted_transaction = transactions.pop(index)

                save_transactions()

                self.send_json(
                    200,
                    {
                        "message": "Transaction deleted successfully",
                        "transaction": deleted_transaction
                    }
                )
                return

        self.send_json(
            404,
            {"error": "Transaction not found"}
        )


if __name__ == "__main__":

    server = HTTPServer(
        ("localhost", 8000),
        TransactionHandler
    )

    print(
        "MoMo REST API running on http://localhost:8000"
    )

    server.serve_forever()
