# Intermediate Tutorial: Building a Real Application

In this tutorial, you'll build a production-feature application — a collaborative note-taking app — adding authentication, database models, background tasks, file uploads, and WebSocket real-time chat.

## Project setup

```bash
aq init notepod
mkdir -p modules/notes/{controllers,services,models,blueprints,tasks}
mkdir -p modules/chat/{controllers,socket_controllers}
mkdir -p uploads
```

## Step 1: Workspace with multiple integrations

`workspace.py`:

```python
from aquilia.workspace import Workspace, Module
from aquilia import AquilaConfig, Secret, Env
from aquilia.integrations import (
    DatabaseIntegration,
    AuthIntegration,
    TasksIntegration,
    StorageIntegration,
    CorsIntegration,
    OpenAPIIntegration,
)

class BaseEnv(AquilaConfig):
    env = "dev"

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000
        reload = True

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        access_token_ttl_minutes = 180
        password_hasher = AquilaConfig.PasswordHasher.argon2id(
            time_cost=3,
            memory_cost=131072,
        )

class DevEnv(BaseEnv):
    env = "dev"

workspace = (
    Workspace("notepod", version="1.0.0")
    .runtime(mode="dev", port=8000, reload=True)
    .module(
        Module("notes", version="0.1.0")
        .route_prefix("/api/notes")
        .depends_on("auth")
    )
    .module(
        Module("auth", version="0.1.0")
        .route_prefix("/auth")
    )
    .module(
        Module("chat", version="0.1.0")
        .route_prefix("/api/chat")
    )
    .integrate(DatabaseIntegration(url="sqlite:///notepod.db"))
    .integrate(AuthIntegration(secret_key="dev-secret-key-change-in-prod"))
    .integrate(TasksIntegration(num_workers=2, max_retries=3))
    .integrate(StorageIntegration(
        default="local",
        backends={
            "local": {"backend": "local", "root": "./uploads"},
        },
    ))
    .integrate(CorsIntegration(allow_origins=["http://localhost:3000"]))
    .integrate(OpenAPIIntegration(
        title="Notepod API",
        version="1.0.0",
        description="Collaborative note-taking API",
    ))
    .env_config(BaseEnv)
)
```

## Step 2: Database model

`modules/notes/models.py`:

```python
from aquilia.models import Model, CharField, TextField, DateTimeField, ForeignKey
from datetime import datetime, timezone


class Note(Model):
    title = CharField(max_length=200)
    content = TextField()
    author_id = CharField(max_length=50)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table = "notes"
        ordering = ["-created_at"]


class NoteAttachment(Model):
    note = ForeignKey(Note, on_delete="CASCADE", related_name="attachments")
    filename = CharField(max_length=255)
    storage_key = CharField(max_length=500)
    content_type = CharField(max_length=100)
    size = CharField(max_length=20)  # IntegerField preferred in real code
    uploaded_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table = "note_attachments"
```

Register models in `modules/notes/manifest.py`:

```python
from aquilia.manifest import AppManifest, BackgroundTaskConfig

manifest = AppManifest(
    name="notes",
    version="0.1.0",
    controllers=[
        "modules.notes.controllers:NotesController",
    ],
    services=[
        "modules.notes.services:NoteService",
    ],
    models=[
        "modules.notes.models:Note",
        "modules.notes.models:NoteAttachment",
    ],
    background_tasks=BackgroundTaskConfig(
        tasks=[
            "modules.notes.tasks:process_attachment",
            "modules.notes.tasks:sync_note_index",
        ],
        default_queue="notes",
    ),
    exports=["NoteService"],
    imports=["auth"],
)
```

## Step 3: Note service with DI

`modules/notes/services.py`:

```python
from __future__ import annotations
from aquilia import Inject
from aquilia.db import AquiliaDatabase
from aquilia.storage import StorageRegistry, StorageFile
from .models import Note, NoteAttachment


class NoteService:

    def __init__(
        self,
        db: AquiliaDatabase = Inject(),
        storage: StorageRegistry = Inject(),
    ):
        self.db = db
        self.storage = storage
        self._backend = self.storage.backend("local")

    async def list_notes(self, author_id: str) -> list[dict]:
        notes = await Note.objects.filter(author_id=author_id).all()
        return [note.to_dict() for note in notes]

    async def get_note(self, note_id: int) -> Note | None:
        return await Note.objects.get_or_none(id=note_id)

    async def create_note(self, author_id: str, title: str, content: str) -> Note:
        note = Note(
            title=title,
            content=content,
            author_id=author_id,
        )
        await note.save()
        return note

    async def update_note(self, note_id: int, author_id: str, **fields) -> Note | None:
        note = await Note.objects.get_or_none(id=note_id)
        if note is None or note.author_id != author_id:
            return None
        for key, value in fields.items():
            setattr(note, key, value)
        await note.save()
        return note

    async def delete_note(self, note_id: int, author_id: str) -> bool:
        note = await Note.objects.get_or_none(id=note_id)
        if note is None or note.author_id != author_id:
            return False
        await note.delete()
        return True

    async def upload_attachment(
        self, note_id: int, filename: str, content_type: str, data: bytes
    ) -> NoteAttachment:
        storage_key = f"notes/{note_id}/{filename}"
        storage_file = StorageFile(
            key=storage_key,
            data=data,
            content_type=content_type,
        )
        await self._backend.put(storage_file)

        attachment = NoteAttachment(
            note_id=note_id,
            filename=filename,
            storage_key=storage_key,
            content_type=content_type,
            size=str(len(data)),
        )
        await attachment.save()
        return attachment
```

## Step 4: Background tasks

`modules/notes/tasks.py`:

```python
from aquilia.tasks import task

@task(queue="notes", max_retries=3)
async def process_attachment(storage_key: str):
    """
    Post-process uploaded files: generate thumbnails, scan for malware, etc.
    This runs asynchronously so the upload response is fast.
    """
    # Simulate processing
    import asyncio
    await asyncio.sleep(2)
    # In production: generate thumbnails, virus scan, extract text, etc.
    return {"status": "processed", "key": storage_key}

@task(queue="notes", interval=300)  # Run every 5 minutes
async def sync_note_index():
    """
    Periodically rebuild the full-text search index for notes.
    """
    # In production: update Elasticsearch/Meilisearch index
    return {"indexed": 0}
```

## Step 5: Auth controller

`modules/auth/controllers.py`:

```python
from aquilia import Controller, POST, GET, RequestCtx, Response, Inject
from aquilia.auth.manager import AuthManager
from aquilia.controller.validation import validate_body
from aquilia.blueprints import Blueprint, TextFacet, EmailFacet
from aquilia.faults.domains import UnauthorizedFault, BadRequestFault


class RegisterBlueprint(Blueprint):
    email = EmailFacet()
    password = TextFacet(min_length=8, max_length=128)
    display_name = TextFacet(max_length=100, required=False)


class LoginBlueprint(Blueprint):
    email = EmailFacet()
    password = TextFacet()


class AuthController(Controller):
    prefix = "/auth"

    def __init__(self, auth_manager: AuthManager = Inject()):
        self.auth = auth_manager

    @POST("/register")
    @validate_body(RegisterBlueprint)
    async def register(self, ctx: RequestCtx, body: dict):
        # Registration logic here — create identity, hash password
        # Simplified: use sign_in with auto-provisioning
        try:
            result = await self.auth.sign_in(
                username=body["email"],
                password=body["password"],
            )
            return Response.json(result.to_dict(), status=201)
        except Exception as e:
            raise BadRequestFault(detail=str(e))

    @POST("/login")
    @validate_body(LoginBlueprint)
    async def login(self, ctx: RequestCtx, body: dict):
        try:
            result = await self.auth.sign_in(
                username=body["email"],
                password=body["password"],
            )
            return Response.json(result.to_dict())
        except Exception:
            raise UnauthorizedFault(detail="Invalid credentials")

    @POST("/logout")
    async def logout(self, ctx: RequestCtx):
        await self.auth.sign_out(scope="all")
        return Response.json({"logged_out": True})

    @GET("/me")
    async def me(self, ctx: RequestCtx):
        if ctx.identity is None:
            raise UnauthorizedFault()
        return Response.json(ctx.identity.to_dict())

    @POST("/refresh")
    async def refresh(self, ctx: RequestCtx):
        refresh_token = ctx.request.json().get("refresh_token")
        if not refresh_token:
            raise BadRequestFault(detail="refresh_token required")
        access, refresh = await self.auth.refresh_access_token(refresh_token)
        return Response.json({
            "access_token": access,
            "refresh_token": refresh,
        })
```

## Step 6: Notes controller with auth + file uploads

`modules/notes/controllers.py`:

```python
from __future__ import annotations

from aquilia import Controller, POST, GET, PUT, DELETE, RequestCtx, Response, Inject
from aquilia.controller.validation import validate_body
from aquilia.faults.domains import NotFoundFault, ForbiddenFault
from aquilia.blueprints import Blueprint, TextFacet
from aquilia import authenticated

from .services import NoteService
from .tasks import process_attachment


class CreateNoteBlueprint(Blueprint):
    title = TextFacet(min_length=1, max_length=200)
    content = TextFacet(max_length=50000)


class UpdateNoteBlueprint(Blueprint):
    title = TextFacet(min_length=1, max_length=200, required=False)
    content = TextFacet(max_length=50000, required=False)


class NotesController(Controller):
    prefix = "/api/notes"
    tags = ["notes"]

    def __init__(self, note_service: NoteService = Inject()):
        self.service = note_service

    @authenticated
    @GET("/")
    async def list_notes(self, ctx: RequestCtx):
        notes = await self.service.list_notes(ctx.identity.id)
        return Response.json({"notes": notes})

    @authenticated
    @GET("/{id:int}")
    async def get_note(self, ctx: RequestCtx, id: int):
        note = await self.service.get_note(id)
        if note is None:
            raise NotFoundFault(detail=f"Note {id} not found")
        return Response.json(note.to_dict())

    @authenticated
    @POST("/")
    @validate_body(CreateNoteBlueprint)
    async def create_note(self, ctx: RequestCtx, body: dict):
        note = await self.service.create_note(
            author_id=ctx.identity.id,
            title=body["title"],
            content=body["content"],
        )
        return Response.json(note.to_dict(), status=201)

    @authenticated
    @PUT("/{id:int}")
    @validate_body(UpdateNoteBlueprint)
    async def update_note(self, ctx: RequestCtx, id: int, body: dict):
        note = await self.service.update_note(
            note_id=id,
            author_id=ctx.identity.id,
            **body,
        )
        if note is None:
            raise NotFoundFault(detail=f"Note {id} not found")
        return Response.json(note.to_dict())

    @authenticated
    @DELETE("/{id:int}")
    async def delete_note(self, ctx: RequestCtx, id: int):
        deleted = await self.service.delete_note(id, ctx.identity.id)
        if not deleted:
            raise NotFoundFault(detail=f"Note {id} not found")
        return Response.json({"deleted": True})

    @authenticated
    @POST("/{id:int}/upload")
    async def upload_attachment(self, ctx: RequestCtx, id: int):
        note = await self.service.get_note(id)
        if note is None or note.author_id != ctx.identity.id:
            raise NotFoundFault()

        form = await ctx.request.form()
        file = form.get("file")
        if not file:
            raise ForbiddenFault(detail="No file provided")

        attachment = await self.service.upload_attachment(
            note_id=id,
            filename=file.filename,
            content_type=file.content_type,
            data=await file.read(),
        )

        # Kick off async processing
        await process_attachment.delay(storage_key=attachment.storage_key)

        return Response.json(attachment.to_dict(), status=201)
```

## Step 7: WebSocket chat

`modules/chat/socket_controllers/chat.py`:

```python
from aquilia.sockets import (
    SocketController, Socket, OnConnect, OnDisconnect, Event, SocketGuard,
)


class ChatController(SocketController):
    """Real-time WebSocket chat controller."""
    prefix = "/ws/chat"

    _connected: dict[str, list] = {}  # room_name → [websocket, ...]

    @OnConnect
    async def on_connect(self, socket: Socket):
        room = socket.query_params.get("room", "general")
        socket.room = room
        self._connected.setdefault(room, []).append(socket)
        await socket.broadcast(room, {
            "type": "user_joined",
            "room": room,
            "users": len(self._connected.get(room, [])),
        })

    @OnDisconnect
    async def on_disconnect(self, socket: Socket):
        room = getattr(socket, "room", "general")
        group = self._connected.get(room, [])
        if socket in group:
            group.remove(socket)

    @Event("message")
    async def handle_message(self, socket: Socket, data: dict):
        room = getattr(socket, "room", "general")
        message = data.get("text", "")
        await socket.broadcast(room, {
            "type": "message",
            "text": message,
            "user": socket.id[:8],
            "room": room,
        })

    @Event("typing")
    async def handle_typing(self, socket: Socket, data: dict):
        room = getattr(socket, "room", "general")
        await socket.broadcast(room, {
            "type": "typing",
            "user": socket.id[:8],
            "room": room,
        })
```

Register in `modules/chat/manifest.py`:

```python
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="chat",
    version="0.1.0",
    socket_controllers=[
        "modules.chat.socket_controllers:ChatController",
    ],
)
```

## Step 8: Testing authenticated endpoints

```python
import pytest
from aquilia.testing import TestClient
from aquilia.entrypoint import create_app

@pytest.fixture
async def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
async def auth_headers(client):
    """Register, login, and return auth headers."""
    await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123",
    })
    resp = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "securepass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_authenticated_note_creation(client, auth_headers):
    resp = await client.post(
        "/api/notes/",
        json={"title": "Meeting notes", "content": "Discuss Q3 roadmap"},
        headers=auth_headers,
    )
    assert resp.status == 201
    assert resp.json()["title"] == "Meeting notes"

@pytest.mark.asyncio
async def test_unauthenticated_access(client):
    resp = await client.get("/api/notes/")
    assert resp.status == 401

@pytest.mark.asyncio
async def test_file_upload(client, auth_headers):
    # Create a note first
    note_resp = await client.post(
        "/api/notes/",
        json={"title": "With attachment", "content": "Some content"},
        headers=auth_headers,
    )
    note_id = note_resp.json()["id"]

    # Upload a file
    resp = await client.post(
        f"/api/notes/{note_id}/upload",
        data={"file": ("test.txt", b"Hello World", "text/plain")},
        headers=auth_headers,
    )
    assert resp.status == 201
    assert resp.json()["filename"] == "test.txt"
```

## Summary

You've built an application with:

| Feature | Implementation |
|---------|---------------|
| Auth | `AuthManager`, `Identity`, JWT tokens, sign_in/sign_out |
| Database | `Model`, `AquiliaDatabase`, ORM queries |
| Background tasks | `@task` decorator, `TaskManager`, periodic sync |
| File uploads | `StorageRegistry`, `StorageFile`, `LocalStorage` |
| WebSocket chat | `SocketController`, `OnConnect`, `Event` |
| API docs | `OpenAPIIntegration` → Swagger UI at `/docs` |
| CORS | `CorsIntegration` for frontend |
| Tests | `TestClient` with auth headers, file uploads |

Access your API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).