"""
Auth module controllers (request handlers).

This file defines the HTTP endpoints for the auth module
using the modern Controller architecture with pattern-based routing.

Endpoints:

File Storage:
* ``POST   /auth/files/upload``             – Upload a file to storage
* ``POST   /auth/files/avatar/<user_id>``   – Upload user avatar
* ``POST   /auth/files/document``           – Upload a document
* ``GET    /auth/files/``                   – List files in a directory
* ``GET    /auth/files/info``               – Get file metadata
* ``GET    /auth/files/download``           – Download / read a file
* ``DELETE /auth/files/delete``             – Delete a file
* ``GET    /auth/files/health``             – Storage health check

ML inference:
* ``POST /auth/ml/login-risk``       – LoginRiskClassifier
* ``POST /auth/ml/anomaly``          – AnomalyDetector
* ``POST /auth/ml/brute-force``      – BruteForceDetector
* ``POST /auth/ml/user-behavior``    – UserBehaviorClassifier
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import AuthNotFoundFault
from .services import AuthService, FileStorageService
from .pipelines import (
    LoginRiskClassifier,
    AnomalyDetector,
    BruteForceDetector,
    UserBehaviorClassifier,
)
from aquilia.faults import UnauthorizedFault

class AuthController(Controller):
    """
    Controller for auth endpoints.

    Provides RESTful CRUD operations for auth plus ML inference endpoints.
    """
    prefix = "/"
    tags = ["auth"]

    def __init__(self, service: "AuthService" = None, file_service: "FileStorageService" = None):
        # Instantiate service directly if not injected
        self.service = service or AuthService()
        self.file_service = file_service

        # ML pipeline instances (loaded lazily on first call)
        self._login_risk: LoginRiskClassifier | None = None
        self._anomaly: AnomalyDetector | None = None
        self._brute_force: BruteForceDetector | None = None
        self._user_behavior: UserBehaviorClassifier | None = None

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _get_login_risk(self) -> LoginRiskClassifier:
        if self._login_risk is None:
            self._login_risk = LoginRiskClassifier()
            await self._login_risk.load("", "cpu")
        return self._login_risk

    async def _get_anomaly(self) -> AnomalyDetector:
        if self._anomaly is None:
            self._anomaly = AnomalyDetector()
            await self._anomaly.load("", "cpu")
        return self._anomaly

    async def _get_brute_force(self) -> BruteForceDetector:
        if self._brute_force is None:
            self._brute_force = BruteForceDetector()
            await self._brute_force.load("", "cpu")
        return self._brute_force

    async def _get_user_behavior(self) -> UserBehaviorClassifier:
        if self._user_behavior is None:
            self._user_behavior = UserBehaviorClassifier()
            await self._user_behavior.load("", "cpu")
        return self._user_behavior

    # ── File Storage endpoints ────────────────────────────────────────────

    @GET("/")
    async def main(self, ctx: RequestCtx):
        raise UnauthorizedFault(detail="Please provide valid credentials to access auth endpoints.")

    @POST("/files/upload")
    async def upload_file(self, ctx: RequestCtx):
        """
        Upload a file to storage.

        Accepts multipart/form-data with a ``file`` field.
        Optional form fields: ``backend`` (default: 'uploads'),
        ``directory`` (sub-path).

        Example::

            POST /auth/files/upload
            Content-Type: multipart/form-data
            file: <binary>
            backend: uploads
            directory: reports/2026

            -> {
                "name": "20260307..._abc123.pdf",
                "path": "reports/2026/20260307..._abc123.pdf",
                "size": 102400,
                "size_human": "100.0 KB",
                "content_type": "application/pdf",
                "backend": "uploads",
                "url": "/storage/uploads/reports/2026/...",
                "uploaded_at": "2026-03-07T..."
            }
        """
        form_data = await ctx.multipart()
        file = form_data.get_file("file")
        if not file:
            return Response.json({"error": "No file provided"}, status=400)

        backend = form_data.get_field("backend") or "uploads"
        directory = form_data.get_field("directory") or ""

        result = await self.file_service.upload_file(
            filename=file.filename,
            content=await file.read(),
            backend_name=backend,
            directory=directory,
        )
        return Response.json(result, status=201)

    @POST("/files/avatar/<user_id:int>")
    async def upload_avatar(self, ctx: RequestCtx, user_id: int):
        """
        Upload a user avatar image.

        Only images allowed (jpeg, png, gif, webp, svg). Max 2 MB.
        Stored in the ``avatars`` backend under ``user_<id>/``.

        Example::

            POST /auth/files/avatar/42
            Content-Type: multipart/form-data
            file: <image binary>

            -> {"name": "...", "path": "user_42/...", "backend": "avatars", ...}
        """
        form_data = await ctx.multipart()
        file = form_data.get_file("file")
        if not file:
            return Response.json({"error": "No file provided"}, status=400)

        result = await self.file_service.upload_avatar(
            user_id=user_id,
            filename=file.filename,
            content=await file.read(),
        )
        return Response.json(result, status=201)

    @POST("/files/document")
    async def upload_document(self, ctx: RequestCtx):
        """
        Upload a document (PDF, Word, text, CSV, etc.).

        Max 25 MB. Stored in the ``documents`` backend.

        Example::

            POST /auth/files/document
            Content-Type: multipart/form-data
            file: <document binary>
            directory: invoices/2026

            -> {"name": "...", "backend": "documents", ...}
        """
        form_data = await ctx.multipart()
        file = form_data.get_file("file")
        if not file:
            return Response.json({"error": "No file provided"}, status=400)

        directory = form_data.get_field("directory") or ""

        result = await self.file_service.upload_document(
            filename=file.filename,
            content=await file.read(),
            directory=directory,
        )
        return Response.json(result, status=201)

    @GET("/files/")
    async def list_files(self, ctx: RequestCtx):
        """
        List files and directories in storage.

        Query params: ``backend`` (default: 'uploads'), ``directory`` (default: root).

        Example::

            GET /auth/files/?backend=uploads&directory=reports

            -> {
                "backend": "uploads",
                "directory": "reports",
                "directories": ["2025", "2026"],
                "files": [{"name": "summary.pdf", "size": 4096, ...}],
                "total_files": 1,
                "total_dirs": 2
            }
        """
        backend = ctx.query_param("backend", "uploads")
        directory = ctx.query_param("directory", "")

        result = await self.file_service.list_files(
            directory=directory,
            backend_name=backend,
        )
        return Response.json(result)

    @GET("/files/info")
    async def file_info(self, ctx: RequestCtx):
        """
        Get detailed metadata for a single file.

        Query params: ``path`` (required), ``backend`` (default: 'uploads').

        Example::

            GET /auth/files/info?path=reports/summary.pdf&backend=uploads

            -> {
                "name": "summary.pdf",
                "path": "reports/summary.pdf",
                "size": 4096,
                "content_type": "application/pdf",
                "last_modified": "...",
                "url": "/storage/uploads/reports/summary.pdf"
            }
        """
        path = ctx.query_param("path", "")
        backend = ctx.query_param("backend", "uploads")

        if not path:
            return Response.json({"error": "Missing 'path' parameter"}, status=400)

        result = await self.file_service.file_info(
            path=path,
            backend_name=backend,
        )
        return Response.json(result)

    @GET("/files/download")
    async def download_file(self, ctx: RequestCtx):
        """
        Download a file from storage.

        Query params: ``path`` (required), ``backend`` (default: 'uploads').
        Returns the raw file bytes with correct Content-Type header.

        Example::

            GET /auth/files/download?path=reports/summary.pdf

            -> <binary PDF content>
        """
        path = ctx.query_param("path", "")
        backend = ctx.query_param("backend", "uploads")

        if not path:
            return Response.json({"error": "Missing 'path' parameter"}, status=400)

        result = await self.file_service.download_file(
            path=path,
            backend_name=backend,
        )
        return Response(
            content=result["content"],
            status=200,
            headers={
                "Content-Disposition": f'attachment; filename="{result["name"]}"',
                "Content-Length": str(result["size"]),
            },
            media_type=result["content_type"],
        )

    @DELETE("/files/delete")
    async def delete_file(self, ctx: RequestCtx):
        """
        Delete a file from storage.

        Query params: ``path`` (required), ``backend`` (default: 'uploads').

        Example::

            DELETE /auth/files/delete?path=reports/old_report.pdf

            -> {"deleted": true, "path": "reports/old_report.pdf", ...}
        """
        path = ctx.query_param("path", "")
        backend = ctx.query_param("backend", "uploads")

        if not path:
            return Response.json({"error": "Missing 'path' parameter"}, status=400)

        result = await self.file_service.delete_file(
            path=path,
            backend_name=backend,
        )
        return Response.json(result)

    @GET("/files/health")
    async def storage_health(self, ctx: RequestCtx):
        """
        Check health of all storage backends.

        Example::

            GET /auth/files/health

            -> {
                "status": "healthy",
                "backends": {
                    "uploads": {"healthy": true, "backend_type": "local"},
                    "avatars": {"healthy": true, "backend_type": "local"},
                    "documents": {"healthy": true, "backend_type": "local"},
                    "temp": {"healthy": true, "backend_type": "memory"}
                },
                "total_backends": 4,
                "healthy_count": 4
            }
        """
        result = await self.file_service.storage_health()
        return Response.json(result)

    # ── ML inference endpoints ────────────────────────────────────────────────

    @POST("/ml/login-risk")
    async def predict_login_risk(self, ctx: RequestCtx):
        """
        Score a login attempt for risk.

        Example::

            POST /auth/ml/login-risk
            {
                "failed_attempts": 5,
                "ip": "203.0.113.42",
                "hour_of_day": 3,
                "new_device": true,
                "vpn_proxy": false,
                "geo_distance_km": 8500,
                "time_since_last_ok": 259200
            }
            -> {"risk_label": "high", "risk_score": 0.91, "probabilities": {...}}
        """
        data = await ctx.json()
        pipeline = await self._get_login_risk()
        result = await pipeline.predict(data)
        return Response.json(result)

    @POST("/ml/anomaly")
    async def detect_anomaly(self, ctx: RequestCtx):
        """
        Detect anomalous session / auth patterns.

        Example::

            POST /auth/ml/anomaly
            {
                "requests_per_minute": 350,
                "unique_endpoints": 42,
                "session_age_seconds": 12,
                "error_rate": 0.45,
                "payload_size_mean": 12000,
                "ip_entropy": 0.88
            }
            -> {"is_anomaly": true, "anomaly_score": -0.312, "verdict": "anomaly"}
        """
        data = await ctx.json()
        pipeline = await self._get_anomaly()
        result = await pipeline.predict(data)
        return Response.json(result)

    @POST("/ml/brute-force")
    async def detect_brute_force(self, ctx: RequestCtx):
        """
        Detect brute-force / credential-stuffing attacks.

        Example::

            POST /auth/ml/brute-force
            {
                "attempts_last_1m": 15,
                "attempts_last_5m": 60,
                "attempts_last_15m": 180,
                "distinct_usernames": 30,
                "distinct_ips": 3,
                "inter_attempt_secs": 0.8,
                "is_known_bad_ip": false
            }
            -> {"is_brute_force": true, "confidence": 0.97, "verdict": "brute_force"}
        """
        data = await ctx.json()
        pipeline = await self._get_brute_force()
        result = await pipeline.predict(data)
        return Response.json(result)

    @POST("/ml/user-behavior")
    async def classify_user_behavior(self, ctx: RequestCtx):
        """
        Classify long-term user behaviour for adaptive auth decisions.

        Example::

            POST /auth/ml/user-behavior
            {
                "avg_session_duration": 45,
                "avg_requests_per_sess": 800,
                "login_hour_mode": "night",
                "device_change_rate": 1.0,
                "mfa_pass_rate": 0.2,
                "days_since_pw_change": 1,
                "failed_login_rate": 0.6
            }
            -> {"behavior_label": "compromised", "behavior_score": 0.87, ...}
        """
        data = await ctx.json()
        pipeline = await self._get_user_behavior()
        result = await pipeline.predict(data)
        return Response.json(result)
