import os
import uuid
import json
import time
from typing import Optional

import requests


BASE_URL = os.getenv("CENTRAL_BASE_URL", "http://localhost:8080")
TIMEOUT = float(os.getenv("CENTRAL_HTTP_TIMEOUT", "10"))


def post_json(path: str, payload: dict) -> requests.Response:
	url = f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"
	headers = {"Content-Type": "application/json"}
	return requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)


def register_citizen(
	*,
	first_name: str,
	last_name: str,
	email: str,
	password: str,
	gov_id: Optional[str] = None,
) -> requests.Response:
	payload = {
		"firstName": first_name,
		"lastName": last_name,
		"email": email,
		"password": password,
	}
	if gov_id:
		payload["govId"] = gov_id
	return post_json("/auth/register/citizen", payload)


def register_business(
	*,
	business_name: str,
	business_reg_id: str,
	email: str,
	password: str,
	province: str,
	city: str,
	address1: str,
	longitude: Optional[float] = None,
	latitude: Optional[float] = None,
) -> requests.Response:
	payload = {
		"businessName": business_name,
		"businessRegId": business_reg_id,
		"email": email,
		"password": password,
		"province": province,
		"city": city,
		"address1": address1,
	}
	if longitude is not None:
		payload["longitude"] = longitude
	if latitude is not None:
		payload["latitude"] = latitude
	return post_json("/auth/register/business", payload)


def pretty(obj) -> str:
	try:
		return json.dumps(obj, indent=2, ensure_ascii=False)
	except Exception:
		return str(obj)


def main() -> None:
	print(f"Using base URL: {BASE_URL}")

	# --- Citizen registration test ---
	citizen_email = f"cit_{uuid.uuid4().hex[:8]}@example.com"
	gov_id = f"GOV{uuid.uuid4().hex[:6]}"

	print("\nRegistering citizen (expected 201)...")
	r1 = register_citizen(
		first_name="John",
		last_name="Doe",
		email=citizen_email,
		password="s3cret",
		gov_id=gov_id,
	)
	print(f"Status: {r1.status_code}")
	print(pretty(r1.json() if r1.headers.get('content-type','').startswith('application/json') else r1.text))

	print("\nRegistering same citizen again (expected 409)...")
	r2 = register_citizen(
		first_name="John",
		last_name="Doe",
		email=citizen_email,  # duplicate email
		password="s3cret",
		gov_id=gov_id,        # duplicate govId
	)
	print(f"Status: {r2.status_code}")
	print(pretty(r2.json() if r2.headers.get('content-type','').startswith('application/json') else r2.text))

	# --- Business registration test ---
	business_email = f"biz_{uuid.uuid4().hex[:6]}@example.com"
	business_reg_id = f"BR{uuid.uuid4().hex[:6]}"

	print("\nRegistering business (expected 201)...")
	b1 = register_business(
		business_name="Acme Store",
		business_reg_id=business_reg_id,
		email=business_email,
		password="pw",
		province="Western Cape",
		city="Cape Town",
		address1="123 Main",
	)
	print(f"Status: {b1.status_code}")
	print(pretty(b1.json() if b1.headers.get('content-type','').startswith('application/json') else b1.text))

	print("\nRegistering same business again (expected 409)...")
	b2 = register_business(
		business_name="Acme Store",
		business_reg_id=business_reg_id,  # duplicate
		email=business_email,              # duplicate
		password="pw",
		province="Western Cape",
		city="Cape Town",
		address1="123 Main",
	)
	print(f"Status: {b2.status_code}")
	print(pretty(b2.json() if b2.headers.get('content-type','').startswith('application/json') else b2.text))


if __name__ == "__main__":
	main()

