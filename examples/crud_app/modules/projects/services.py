from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from aquilia.faults import ConflictFault, NotFoundFault


@dataclass(slots=True)
class ProjectRecord:
    key: str
    name: str
    owner_email: str
    summary: str | None = None
    status: str = "planned"
    archived: bool = False
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProjectRepository:
    def __init__(self):
        self._rows: dict[str, ProjectRecord] = {}

    async def list(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        rows = list(self._rows.values())
        if not include_archived:
            rows = [row for row in rows if not row.archived]
        rows.sort(key=lambda row: row.updated_at, reverse=True)
        return [row.to_dict() for row in rows]

    async def get(self, key: str) -> dict[str, Any]:
        row = self._rows.get(key.upper())
        if row is None:
            raise NotFoundFault(detail=f"Project {key!r} was not found")
        return row.to_dict()

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        key = data["key"].upper()
        if key in self._rows:
            raise ConflictFault(detail=f"Project {key!r} already exists")
        row = ProjectRecord(**data)
        self._rows[key] = row
        return row.to_dict()

    async def update(self, key: str, changes: dict[str, Any]) -> dict[str, Any]:
        row = self._rows.get(key.upper())
        if row is None:
            raise NotFoundFault(detail=f"Project {key!r} was not found")
        for field, value in changes.items():
            if value is not None and hasattr(row, field):
                setattr(row, field, value)
        row.updated_at = datetime.now(timezone.utc).isoformat()
        return row.to_dict()


class ProjectsService:
    def __init__(self, repository: ProjectRepository | None = None):
        self.repository = repository or ProjectRepository()

    async def list_projects(self, include_archived: bool = False):
        return await self.repository.list(include_archived=include_archived)

    async def create_project(self, data: dict[str, Any]):
        return await self.repository.create(data)

    async def get_project(self, key: str):
        return await self.repository.get(key)

    async def update_project(self, key: str, changes: dict[str, Any]):
        return await self.repository.update(key, changes)

    async def archive_project(self, key: str):
        return await self.repository.update(key, {"archived": True, "status": "archived"})

    async def restore_project(self, key: str):
        return await self.repository.update(key, {"archived": False, "status": "active"})
