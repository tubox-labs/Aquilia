"""
Auth module controllers (request handlers).

This file defines the HTTP endpoints for the auth module
using the modern Controller architecture with pattern-based routing.

ML inference endpoints are also provided via the four sklearn pipelines
defined in ``pipelines.py``:

* ``POST /auth/ml/login-risk``       – LoginRiskClassifier
* ``POST /auth/ml/anomaly``          – AnomalyDetector
* ``POST /auth/ml/brute-force``      – BruteForceDetector
* ``POST /auth/ml/user-behavior``    – UserBehaviorClassifier
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import AuthNotFoundFault
from .services import AuthService
from .pipelines import (
    LoginRiskClassifier,
    AnomalyDetector,
    BruteForceDetector,
    UserBehaviorClassifier,
)


class AuthController(Controller):
    """
    Controller for auth endpoints.

    Provides RESTful CRUD operations for auth plus ML inference endpoints.
    """
    prefix = "/"
    tags = ["auth"]

    def __init__(self, service: "AuthService" = None):
        # Instantiate service directly if not injected
        self.service = service or AuthService()

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

    @GET("/")
    async def list_auth(self, ctx: RequestCtx):
        """
        List all auth.

        Example:
            GET /auth/ -> {"items": [...], "total": 0}
        """
        items = await self.service.get_all()

        raise AuthNotFoundFault(1)

    @POST("/")
    async def create_auth(self, ctx: RequestCtx):
        """
        Create a new auth.

        Example:
            POST /auth/
            Body: {"name": "Example"}
            -> {"id": 1, "name": "Example"}
        """
        data = await ctx.json()
        item = await self.service.create(data)
        return Response.json(item, status=201)

    @GET("/<id:int>")
    async def get_auth(self, ctx: RequestCtx, id: int):
        """
        Get a auth by ID.

        Example:
            GET /auth/1 -> {"id": 1, "name": "Example"}
        """
        item = await self.service.get_by_id(id)
        if not item:
            raise AuthNotFoundFault(item_id=id)

        return Response.json(item)

    @PUT("/<id:int>")
    async def update_auth(self, ctx: RequestCtx, id: int):
        """
        Update a auth by ID.

        Example:
            PUT /auth/1
            Body: {"name": "Updated"}
            -> {"id": 1, "name": "Updated"}
        """
        data = await ctx.json()
        item = await self.service.update(id, data)
        if not item:
            raise AuthNotFoundFault(item_id=id)

        return Response.json(item)

    @DELETE("/<id:int>")
    async def delete_auth(self, ctx: RequestCtx, id: int):
        """
        Delete a auth by ID.

        Example:
            DELETE /auth/1 -> 204 No Content
        """
        deleted = await self.service.delete(id)
        if not deleted:
            raise AuthNotFoundFault(item_id=id)

        return Response(status=204)

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
