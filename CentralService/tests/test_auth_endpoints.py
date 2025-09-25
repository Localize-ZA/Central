import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from CentralService.auth import router
from Data.models import Base, get_db as models_get_db


def create_test_app_and_db():
    # In-memory SQLite that persists across connections in the same process
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

    # Create tables
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override the dependency used in the router with our testing session
    app.dependency_overrides[models_get_db] = override_get_db
    return app


@pytest.fixture()
def client():
    app = create_test_app_and_db()
    with TestClient(app) as c:
        yield c


def test_register_citizen_success_and_login(client: TestClient):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "firstName": "John",
        "lastName": "Doe",
        "email": email,
        "password": "s3cret",
        "govId": f"GOV{uuid.uuid4().hex[:6]}",
    }

    r = client.post("/register/citizen", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == email
    assert "citizen_id" in body

    # Login success
    lr = client.post("/login/Citizen", json={"email": email, "password": "s3cret"})
    assert lr.status_code == 200, lr.text
    lbody = lr.json()
    assert lbody["email"] == email

    # Wrong password
    lr2 = client.post("/login/Citizen", json={"email": email, "password": "wrong"})
    assert lr2.status_code == 401


def test_register_citizen_duplicate_email_and_govid(client: TestClient):
    email = f"dup_{uuid.uuid4().hex[:6]}@example.com"
    govid = f"GOV{uuid.uuid4().hex[:6]}"
    payload = {
        "firstName": "Jane",
        "lastName": "Smith",
        "email": email,
        "password": "pw",
        "govId": govid,
    }
    r1 = client.post("/register/citizen", json=payload)
    assert r1.status_code == 201, r1.text

    # Duplicate email
    r2 = client.post("/register/citizen", json={**payload, "govId": f"GOV{uuid.uuid4().hex[:6]}"})
    assert r2.status_code == 409, r2.text
    assert "email" in r2.json()["detail"]

    # Duplicate govId
    new_email = f"new_{uuid.uuid4().hex[:6]}@example.com"
    r3 = client.post("/register/citizen", json={**payload, "email": new_email})
    assert r3.status_code == 409, r3.text
    assert "govId" in r3.json()["detail"]


def test_register_business_success_and_duplicate(client: TestClient):
    email = f"biz_{uuid.uuid4().hex[:6]}@example.com"
    regid = f"BR{uuid.uuid4().hex[:6]}"
    payload = {
        "businessName": "Acme Store",
        "businessRegId": regid,
        "email": email,
        "password": "pw",
        "province": "Western Cape",
        "city": "Cape Town",
        "address1": "123 Main",
    }

    r = client.post("/register/business", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == email
    assert body["business_reg_id"] == regid

    # Duplicate email
    r2 = client.post("/register/business", json={**payload, "businessRegId": f"BR{uuid.uuid4().hex[:6]}"})
    assert r2.status_code == 409
    assert "email" in r2.json()["detail"]

    # Duplicate businessRegId
    r3 = client.post("/register/business", json={**payload, "email": f"{uuid.uuid4().hex[:6]}@x.com"})
    assert r3.status_code == 409
    assert "businessRegId" in r3.json()["detail"]
