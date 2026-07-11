from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

# Paths
BENCHMARKS_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = BENCHMARKS_DIR / "datasets"
TECHEMPOWER_DIR = BENCHMARKS_DIR / "techempower"
DB_PATH = TECHEMPOWER_DIR / "techempower.db"
TEMPLATES_DIR = TECHEMPOWER_DIR / "templates"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)


# 1. Deterministic Large JSON Payload (approx 100KB-1MB based on records)
def build_large_payload(records: int = 500) -> dict[str, Any]:
    random.seed(42)
    items = []
    for idx in range(records):
        items.append(
            {
                "id": idx,
                "uuid": f"uuid-{idx:04d}",
                "name": f"record-item-name-{idx}",
                "active": idx % 2 == 0,
                "score": round((idx * 3.14159) % 100, 4),
                "tags": [f"tag-{idx % 7}", f"category-{idx % 13}", "framework-benchmark"],
                "details": {
                    "owner": f"owner-user-{idx % 23}",
                    "cluster": f"us-east-1{chr(97 + (idx % 3))}",
                    "specs": {
                        "cpu_cores": [2, 4, 8, 16][idx % 4],
                        "memory_gb": [4, 8, 16, 32, 64][idx % 5],
                        "storage_tb": round((idx * 0.123) % 4, 2),
                        "backups_enabled": idx % 3 != 0,
                    },
                },
            }
        )
    return {
        "ok": True,
        "payload_type": "large-benchmark-dataset",
        "record_count": records,
        "timestamp": "2026-06-29T23:50:00Z",
        "items": items,
    }


LARGE_PAYLOAD = build_large_payload(500)
LARGE_PAYLOAD_BYTES = json.dumps(LARGE_PAYLOAD).encode("utf-8")

# Ensure large.json is written to disk for static serving / file reads
LARGE_JSON_PATH = DATASETS_DIR / "large.json"
if not LARGE_JSON_PATH.exists():
    LARGE_JSON_PATH.write_text(json.dumps(LARGE_PAYLOAD, indent=2), encoding="utf-8")

# Ensure sample.txt is written to disk
SAMPLE_TEXT_PATH = DATASETS_DIR / "sample.txt"
if not SAMPLE_TEXT_PATH.exists():
    SAMPLE_TEXT_PATH.write_text(
        "Hello, this is a sample text file used for comparative framework file response benchmarks.\n" * 50,
        encoding="utf-8",
    )


# 2. Database Connection Helpers (Async SQLite)
class AsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()


async def get_db_connection():
    import aiosqlite

    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    return AsyncConnectionContext(conn)


# 3. Jinja2 Templating
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


# 4. Validation Schemas

# A. Pydantic (FastAPI / Starlette etc.)
from pydantic import BaseModel, Field


class AddressModel(BaseModel):
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    zipcode: str = Field(min_length=5, max_length=10)


class UserProfileModel(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3)
    age: int = Field(ge=0, le=120)
    tags: list[str]
    address: AddressModel


# B. Standard Dataclasses with Validation (Flask / Django / etc.)
@dataclass
class AddressDataclass:
    street: str
    city: str
    zipcode: str

    def validate(self):
        if not self.street or len(self.street) < 1:
            raise ValueError("Street cannot be empty")
        if not self.city or len(self.city) < 1:
            raise ValueError("City cannot be empty")
        if not self.zipcode or not (5 <= len(self.zipcode) <= 10):
            raise ValueError("Zipcode must be 5-10 chars")


@dataclass
class UserProfileDataclass:
    username: str
    email: str
    age: int
    tags: list[str]
    address: AddressDataclass

    def validate(self):
        if not self.username or not (3 <= len(self.username) <= 50):
            raise ValueError("Username must be 3-50 chars")
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email format")
        if not (0 <= self.age <= 120):
            raise ValueError("Age must be 0-120")
        if not isinstance(self.tags, list):
            raise ValueError("Tags must be a list")
        self.address.validate()

    @classmethod
    def from_dict(cls, data: dict):
        addr_data = data.get("address", {})
        addr = AddressDataclass(
            street=str(addr_data.get("street", "")),
            city=str(addr_data.get("city", "")),
            zipcode=str(addr_data.get("zipcode", "")),
        )
        obj = cls(
            username=str(data.get("username", "")),
            email=str(data.get("email", "")),
            age=int(data.get("age", 0)),
            tags=[str(t) for t in data.get("tags", [])],
            address=addr,
        )
        obj.validate()
        return obj


# C. Aquilia Contract (Aquilia native)
from aquilia.contracts import Contract, NestedContractFacet


class AddressContract(Contract):
    street: str
    city: str
    zipcode: str


class UserProfileContract(Contract):
    username: str
    email: str
    age: int
    tags: list[str]
    address: AddressContract
    address = NestedContractFacet(AddressContract)


# 5. Shared Validation Input Data
VALIDATION_INPUT = {
    "username": "benchmark_user",
    "email": "user@benchmark.com",
    "age": 30,
    "tags": ["speed", "concurrency", "validation"],
    "address": {"street": "123 Framework Boulevard", "city": "API Town", "zipcode": "10001"},
}
VALIDATION_INPUT_BYTES = json.dumps(VALIDATION_INPUT).encode("utf-8")


# 6. Middleware Builder helper (for multi-middleware test)
def build_custom_middleware_stack(app_type: str, layers_count: int):
    """Generates middleware class layers count dynamically."""
    pass
