import asyncio
from aquilia import AquiliaServer, Config
from aquilia.blueprints import Blueprint
from aquilia.blueprints.facets import TextFacet
from aquilia.blueprints.annotations import NestedBlueprintFacet
import os

os.environ['AQUILIA_SIGNING_SECRET'] = 'x' * 32
os.environ['AQUILARY_REGISTRY'] = 'tests/fixtures'

app = AquiliaServer()

class AddressBP(Blueprint):
    city = TextFacet(required=True)

class UserBP(Blueprint):
    name = TextFacet(required=True)
    address = NestedBlueprintFacet(AddressBP, required=True)

@app.router.post("/users")
async def create_user(data: UserBP):
    return {"status": "ok"}

from httpx import AsyncClient

async def run():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        resp = await client.post("/users", json={"name": "Alice", "address": {}})
        print(f"Status Code: {resp.status_code}")
        print(f"Response JSON: {resp.json()}")

if __name__ == "__main__":
    asyncio.run(run())
