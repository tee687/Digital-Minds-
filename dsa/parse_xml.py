import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path

XML_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "modified_sms_v2.xml"
JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "sms_records.json"

PATTERNS = [
    ("received", re.compile(r"You have received ([\d,]+) RWF from (.+?) \(")),
    ("payment",  re.compile(r"Your payment of ([\d,]+) RWF to (.+?) \d+ has been completed")),
    ("transfer", re.compile(r"([\d,]+) RWF transferred to (.+?) \(")),
    ("deposit",  re.compile(r"bank deposit of ([\d,]+) RWF")),
]
DATE_RE = re.compile(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
FEE_RE = re.compile(r"Fee (?:was|paid):? ([\d,]+) RWF")


def parse(path=XML_PATH):
    root = ET.parse(path).getroot()
    records = []
    for i, sms in enumerate(root.findall("sms"), start=1):
        body = sms.get("body", "")
        rec = {"id": i, "type": "other", "amount": None,
               "counterparty": None, "timestamp": None, "fee": None,
               "body": body}
        for name, rx in PATTERNS:
            m = rx.search(body)
            if m:
                rec["type"] = name
                rec["amount"] = int(m.group(1).replace(",", ""))
                rec["counterparty"] = m.group(2) if m.lastindex >= 2 else None
                break
        d = DATE_RE.search(body)
        if d:
            rec["timestamp"] = d.group(1)
        f = FEE_RE.search(body)
        if f:
            rec["fee"] = int(f.group(1).replace(",", ""))
        records.append(rec)
    return records


if __name__ == "__main__":
    records = parse()
    print(f"Parsed {len(records)} records")

    counts = {}
    for r in records:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    print(counts)

    print(records[0])
    JSON_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved to {JSON_PATH}")