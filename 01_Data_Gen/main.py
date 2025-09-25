import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel 
import requests
from dotenv import load_dotenv

class CitizenToBusiness(BaseModel):
    businessRegID: str
    citizenID: str
    products: dict[str, int]  # name, amount
    time: Optional[str] = None

class BusinessToBusiness(BaseModel):
    FromBusinessRegID: str
    ToBusinessRegID: str
    products: dict[str, int]  # name, amount
    time: Optional[str] = None

# Global destination URL loaded from .env (key: MOCK_DATA_URL)
URL: Optional[str] = None


def init() -> None:
    """Load environment variables and initialize globals."""
    global URL
    load_dotenv()
    URL = os.getenv("MOCK_DATA_URL")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rand_amount(min_val: float = 1.0, max_val: float = 1000.0) -> float:
    return round(random.uniform(min_val, max_val), 2)


def _rand_currency() -> str:
    return random.choice(["USD", "EUR", "ZAR", "GBP", "KES", "NGN"])


def _rand_name() -> str:
    first = random.choice(["Alex", "Sam", "Jamie", "Taylor", "Jordan", "Casey", "Riley", "Morgan"])  # noqa: E501
    last = random.choice(["Smith", "Johnson", "Brown", "Williams", "Jones", "Miller", "Davis"])  # noqa: E501
    return f"{first} {last}"


def _rand_phone() -> str:
    return "+27" + str(random.randint(600000000, 799999999))


def _pydantic_dump(model: BaseModel) -> Dict[str, Any]:
    """Return a plain dict from a Pydantic model for v1 or v2."""
    # pydantic v2: model_dump; v1: dict
    dump_fn = getattr(model, "model_dump", None)
    if callable(dump_fn):  # type: ignore[truthy-function]
        return dump_fn()  # type: ignore[no-any-return]
    return model.dict()  # type: ignore[no-any-return]


def gen_iso_8583() -> Dict[str, Any]:
    """Return a simplified ISO 8583-like payload (JSON representation)."""
    stan = random.randint(100000, 999999)  # Systems Trace Audit Number
    rrn = str(uuid.uuid4())[:12].replace("-", "").upper()
    payload = {
        "mti": "0200",
        "processingCode": "000000",
        "amount": int(_rand_amount(5, 500) * 100),  # in minor units
        "transmissionDateTime": datetime.utcnow().strftime("%m%d%H%M%S"),
        "stan": stan,
        "rrn": rrn,
        "cardNumber": "4" + str(random.randint(10**14, 10**15 - 1)),
        "expiry": datetime.utcnow().strftime("%m%y"),
        "posEntryMode": "012",
        "acquirerId": "000001",
        "terminalId": f"TERM{random.randint(1000,9999)}",
        "merchantId": f"MRC{random.randint(100000,999999)}",
        "currency": _rand_currency(),
        "cardholderName": _rand_name(),
        "description": "Purchase",
        "timestamp": _now_iso(),
    }
    return payload


def gen_iso_20022() -> Dict[str, Any]:
    """Return a simplified ISO 20022 pain.001-like payload."""
    tx_id = str(uuid.uuid4())
    debtor = _rand_name()
    creditor = _rand_name()
    amount = _rand_amount(10, 1500)
    currency = _rand_currency()
    payload = {
        "CstmrCdtTrfInitn": {
            "GrpHdr": {
                "MsgId": tx_id,
                "CreDtTm": _now_iso(),
                "NbOfTxs": "1",
            },
            "PmtInf": [
                {
                    "PmtInfId": f"PMT-{tx_id[:8]}",
                    "PmtMtd": "TRF",
                    "ReqdExctnDt": datetime.utcnow().strftime("%Y-%m-%d"),
                    "Dbtr": {"Nm": debtor},
                    "DbtrAcct": {"Id": {"IBAN": f"DE89{random.randint(10**16, 10**17-1)}"}},
                    "Cdtr": {"Nm": creditor},
                    "CdtrAcct": {"Id": {"IBAN": f"GB29{random.randint(10**16, 10**17-1)}"}},
                    "CdtTrfTxInf": [
                        {
                            "PmtId": {"EndToEndId": tx_id},
                            "Amt": {"InstdAmt": {"Ccy": currency, "Value": amount}},
                            "RmtInf": {"Ustrd": ["Invoice payment"]},
                        }
                    ],
                }
            ],
        }
    }
    return payload


def gen_model_citizen_to_business() -> Dict[str, Any]:
    """Generate a CitizenToBusiness payload using the Pydantic model."""
    # Build a small random products dict with 1-3 entries of quantities
    product_names = [
        "Groceries",
        "Airtime",
        "Electricity",
        "Clothing",
        "Fuel",
        "Pharmacy",
    ]
    items = random.sample(product_names, k=random.randint(1, min(3, len(product_names))))
    products = {name: random.randint(1, 5) for name in items}

    model = CitizenToBusiness(
        businessRegID=f"BR{random.randint(100000, 999999)}",
        citizenID=f"CIT{random.randint(1000000, 9999999)}",
        products=products,
        time=_now_iso(),
    )
    return _pydantic_dump(model)


def gen_model_business_to_business() -> Dict[str, Any]:
    """Generate a BusinessToBusiness payload using the Pydantic model."""
    product_names = [
        "WholesaleFood",
        "Electronics",
        "Clothing",
        "Stationery",
        "CleaningSupplies",
    ]
    items = random.sample(product_names, k=random.randint(1, min(3, len(product_names))))
    products = {name: random.randint(1, 20) for name in items}

    model = BusinessToBusiness(
        FromBusinessRegID=f"BR{random.randint(100000, 999999)}",
        ToBusinessRegID=f"BR{random.randint(100000, 999999)}",
        products=products,
        time=_now_iso(),
    )
    return _pydantic_dump(model)


def gen_citizen_to_business() -> Dict[str, Any]:
    """Return a simple CitizenToBusiness JSON object."""
    transaction_id = str(uuid.uuid4())
    amount = _rand_amount(1, 1000)
    currency = _rand_currency()
    payload = {
        "type": "CitizenToBusiness",
        "transactionId": transaction_id,
        "channel": random.choice(["USSD", "APP", "WEB", "POS"]),
        "payer": {
            "name": _rand_name(),
            "msisdn": _rand_phone(),
            "idNumber": str(random.randint(7001010000000, 9912319999999)),
        },
        "payee": {
            "name": random.choice(["Shoprite", "Pick n Pay", "Spar", "Woolworths", "Checkers"]),
            "merchantId": f"MER{random.randint(100000,999999)}",
            "terminalId": f"TERM{random.randint(1000,9999)}",
        },
        "amount": amount,
        "currency": currency,
        "description": random.choice(["Groceries", "Airtime", "Electricity", "Clothing", "Fuel"]),
        "timestamp": _now_iso(),
        "metadata": {
            "reference": f"REF-{transaction_id[:8].upper()}",
            "location": random.choice(["Cape Town", "Johannesburg", "Durban", "Pretoria", "Gqeberha"]),
        },
    }
    return payload


def send_http(body: Dict[str, Any], timeout: float = 10.0) -> Optional[requests.Response]:
    """Send JSON body to MOCK_DATA_URL via HTTP POST."""
    global URL
    if not URL:
        init()
    if not URL:
        print("MOCK_DATA_URL not set in .env. Skipping send.")
        return None

    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(URL, headers=headers, json=body, timeout=timeout)
        return resp
    except Exception as e:  # Network or request exceptions
        print(f"HTTP error: {e}")
        return None


def build_payload(fmt: Literal["iso8583", "iso20022", "c2b", "CitizenToBusiness", "BusinessToBusiness"]) -> Dict[str, Any]:
    if fmt == "iso8583":
        return gen_iso_8583()
    if fmt == "iso20022":
        return gen_iso_20022()
    if fmt == "CitizenToBusiness":
        return gen_model_citizen_to_business()
    if fmt == "BusinessToBusiness":
        return gen_model_business_to_business()
    return gen_citizen_to_business()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and send mock payment data")
    parser.add_argument(
        "--format",
        choices=[
            "iso8583",
            "iso20022",
            "c2b",
            "CitizenToBusiness",
            "BusinessToBusiness",
            "random",
        ],
        default=None,
        help=(
            "Payload format to generate. If omitted, a random number % 3 selects the format: "
            "0=iso8583, 1=iso20022, 2=c2b. Use 'random' to vary per message as well. "
            "Additional options: CitizenToBusiness, BusinessToBusiness for Pydantic-model JSON."
        ),
    )
    parser.add_argument(
        "--interval", "-i", type=float, default=1.0, help="Seconds between messages (default: 1.0)"
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=0,
        help="Number of messages to generate (0 = infinite)",
    )
    parser.add_argument(
        "--dry-run", "--dry_run", action="store_true", help="Print payloads instead of sending"
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON payloads"
    )
    args = parser.parse_args()

    init()

    idx = 0
    try:
        while True:
            idx += 1
            if args.format is None or args.format == "random":
                r = random.randint(0, 2**31 - 1)
                mod = r % 4
                fmt = "iso8583" if mod == 0 else ("iso20022" if mod == 1 else ("c2b" if mod == 2 else ("CitizenToBusiness" if mod == 3  else "BusinessToBusiness")))
            else:
                fmt = args.format
            payload = build_payload(fmt)
            if args.dry_run:
                print(json.dumps(payload, indent=2 if args.pretty else None))
            else:
                resp = send_http(payload)
                status = resp.status_code if resp is not None else "ERR"
                print(f"[{idx}] Sent {fmt} -> status={status}")
            # Stop if a finite count was requested
            if args.count and idx >= args.count:
                break
            if args.interval > 0:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Interrupted by user")


if __name__ == "__main__":
    main()
    