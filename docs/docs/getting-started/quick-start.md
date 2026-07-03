---
title: "Quick Start"
description: "5-minute hello world CRUD/GET setup in Aquilia"
icon: lucide/rocket
---This guide will walk you through a **5-minute end-to-end setup** to define an Aquilia controller, register a blueprint on the response, and build a full "Hello World" level CRUD API.

Aquilia replaces traditional function-based flow handlers with a robust, class-based, metadata-first controller system paired with model-world serialization contracts called Blueprints.

---

## 5-Minute End-to-End GET Setup

Here is how you can set up a controller with a single GET route that returns JSON and applies a response serialization Blueprint.

```python
# hello_controller.py
from aquilia.controller import Controller, GET, RequestCtx
from aquilia.blueprints import Blueprint

# 1. Define a response Blueprint contract
class GreetingBlueprint(Blueprint):
    message: str
    status: str

# 2. Define the Controller and route handler
class HelloController(Controller):
    prefix = "/api"

    @GET("/hello", response_blueprint=GreetingBlueprint)
    async def say_hello(self, ctx: RequestCtx):
        return {
            "message": "Hello, World!",
            "status": "success",
            "ignored_field": "This will be filtered out by the blueprint"
        }
```

!!! info "How Response Blueprints Work"
    When you register `response_blueprint=GreetingBlueprint` on a route decorator, the Aquilia engine intercepts the return dict and automatically filters, validates, and serializes it based on the fields defined in the Blueprint. The `ignored_field` is omitted from the JSON output.


---

## Hello World CRUD/GET Controller

Below is a complete, runnable CRUD controller utilizing an in-memory dictionary to manage resources. This example showcases request payload ingestion, validation, and database updates.

```python
# items_controller.py
from aquilia.controller import Controller, GET, POST, PUT, DELETE, RequestCtx
from aquilia.blueprints import Blueprint

# Simulated database store
ITEMS_DB = {
    1: {"id": 1, "name": "Item A", "price": 10.99},
    2: {"id": 2, "name": "Item B", "price": 20.99},
}

# 1. Define the serialization and validation contract
class ItemBlueprint(Blueprint):
    id: int
    name: str
    price: float

# 2. Create the Controller to handle CRUD operations
class ItemsController(Controller):
    prefix = "/items"

    @GET("/")
    async def list_items(self, ctx: RequestCtx):
        """Retrieve all items."""
        return list(ITEMS_DB.values())

    @GET("/{id:int}")
    async def get_item(self, ctx: RequestCtx, id: int):
        """Retrieve a specific item by ID."""
        item = ITEMS_DB.get(id)
        if not item:
            return {"error": "Item not found"}, 404
        return item

    @POST("/", response_blueprint=ItemBlueprint)
    async def create_item(self, ctx: RequestCtx):
        """Create a new item with request validation."""
        # 1. Read request JSON body
        payload = await ctx.json()
        
        # 2. Bind payload to the Blueprint for validation
        bp = ItemBlueprint(data=payload)
        
        # 3. Check constraints (Seals)
        if not bp.is_sealed():
            return {"errors": bp.errors}, 400
            
        # 4. Save validated data to database
        validated = bp.validated_data
        new_id = max(ITEMS_DB.keys(), default=0) + 1
        new_item = {
            "id": new_id,
            "name": validated["name"],
            "price": validated["price"],
        }
        ITEMS_DB[new_id] = new_item
        return new_item

    @PUT("/{id:int}", response_blueprint=ItemBlueprint)
    async def update_item(self, ctx: RequestCtx, id: int):
        """Update an existing item."""
        if id not in ITEMS_DB:
            return {"error": "Item not found"}, 404
            
        payload = await ctx.json()
        bp = ItemBlueprint(data=payload)
        
        if not bp.is_sealed():
            return {"errors": bp.errors}, 400
            
        validated = bp.validated_data
        ITEMS_DB[id]["name"] = validated["name"]
        ITEMS_DB[id]["price"] = validated["price"]
        return ITEMS_DB[id]

    @DELETE("/{id:int}")
    async def delete_item(self, ctx: RequestCtx, id: int):
        """Delete an item by ID."""
        if id not in ITEMS_DB:
            return {"error": "Item not found"}, 404
        del ITEMS_DB[id]
        return {"success": True}
```

---

## API Verification & Source Citations

All components used in this guide are built on top of Aquilia's verified, first-class APIs:

| Component / API | Verified Source & Module | Description / Reference |
| :--- | :--- | :--- |
| **`Controller`** | [aquilia/controller/\_\_init\_\_.py:L34](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L34) | Class-based handler base class (exported in [L105](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L105)). |
| **`GET` / `POST` / `PUT` / `DELETE`** | [aquilia/controller/\_\_init\_\_.py:L41-47](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L41-L47) | Route decorator classes for handling HTTP verbs (exported in [L111-115](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L111-L115)). |
| **`RequestCtx`** | [aquilia/controller/\_\_init\_\_.py:L34](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L34) | The request context object passed into every handler (exported in [L106](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py#L106)). |
| **`ctx.json()`** | `.cache/index_controller.json:L83-87` | Asynchronous method on `RequestCtx` to extract the parsed JSON body of a request. |
| **`Blueprint`** | [aquilia/blueprints/\_\_init\_\_.py:L41](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/__init__.py#L41) | Declares the serialization & validation contracts (exported in [L112](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/__init__.py#L112)). |
| **`bp.is_sealed()`** | `.cache/index_blueprints.json:L95-100` | Checks if inbound data conforms to the Blueprint constraint seals. |
| **`bp.validated_data`** | `.cache/index_blueprints.json:L130-135` | Property that yields fully validated and parsed inbound data. |
| **`bp.errors`** | `.cache/index_blueprints.json:L137-141` | Property yielding a dictionary of validation faults keyed by field name. |
| **`response_blueprint`** | [aquilia/blueprints/\_\_init\_\_.py:L35](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/__init__.py#L35) | Route-level integration parameter that binds a serializer blueprint directly to the endpoint response. |
