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

