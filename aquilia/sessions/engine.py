"""
AquilaSessions - Session Engine.

The SessionEngine orchestrates the complete session lifecycle:
1. Detection - Extract session ID from transport
2. Resolution - Load from store or create new
3. Validation - Check expiry, idle timeout, absolute timeout, fingerprint
4. Binding - Bind to request context and DI
5. Mutation - Handler reads/writes session data
6. Commit - Persist, rotate, or destroy (concurrency checked BEFORE save)
7. Emission - Transport writes updated reference
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .core import Session, SessionID, SessionScope, SessionFlag
from .faults import (
    SessionExpiredFault,
    SessionIdleTimeoutFault,
    SessionAbsoluteTimeoutFault,
    SessionInvalidFault,
    SessionNotFoundFault,
    SessionConcurrencyViolationFault,
    SessionRotationFailedFault,
    SessionPolicyViolationFault,
    SessionStoreUnavailableFault,
    SessionFingerprintMismatchFault,
)

if TYPE_CHECKING:
    from aquilia.request import Request
    from aquilia.response import Response
    from aquilia.di import Container
    from .policy import SessionPolicy
    from .store import SessionStore
    from .transport import SessionTransport


# ============================================================================
# SessionEngine - Lifecycle Orchestrator
# ============================================================================

class SessionEngine:
    """
    Session lifecycle orchestrator.
    
    The SessionEngine is the central coordinator for all session operations.
    It enforces policy, manages storage, and emits observability events.
    
    Architecture:
        SessionEngine is app-scoped (singleton per app)
        Session instances are request-scoped (created per request)
    """
    
    def __init__(
        self,
        policy: SessionPolicy,
        store: SessionStore,
        transport: SessionTransport,
        logger: logging.Logger | None = None,
    ):
        self.policy = policy
        self.store = store
        self.transport = transport
        self.logger = logger or logging.getLogger("aquilia.sessions")
        self._event_handlers: list = []
    
    # ========================================================================
    # Phase 1 & 2: Detection + Resolution
    # ========================================================================
    
    async def resolve(
        self,
        request: Request,
        container: Container | None = None,
    ) -> Session:
        """
        Resolve session for request (Phase 1-4).
        
        Returns:
            Valid session (existing or new)
        """
        now = datetime.now(timezone.utc)
        
        # Phase 1: Detection
        session_id_str = self.transport.extract(request)
        
        if session_id_str:
            try:
                session_id = SessionID.from_string(session_id_str)
                session = await self._load_existing(session_id, now, request)
                
                if session:
                    self._emit_event("session_loaded", session, request)
                    return session
            
            except ValueError:
                self.logger.warning(f"Invalid session ID format: {session_id_str[:16]}...")
                self._emit_event("session_invalid", None, request)
            
            except SessionExpiredFault:
                self.logger.info(f"Session expired, creating new: {session_id_str[:16]}...")
                self._emit_event("session_expired", None, request)
            
            except SessionIdleTimeoutFault:
                self.logger.info(f"Session idle timeout: {session_id_str[:16]}...")
                self._emit_event("session_idle_timeout", None, request)
            
            except SessionAbsoluteTimeoutFault:
                self.logger.info(f"Session absolute timeout: {session_id_str[:16]}...")
                self._emit_event("session_absolute_timeout", None, request)
            
            except SessionFingerprintMismatchFault:
                self.logger.warning(f"Session fingerprint mismatch (possible hijack): {session_id_str[:16]}...")
                self._emit_event("session_fingerprint_mismatch", None, request)
        
        # Phase 2: Resolution - Create new session
        session = await self._create_new(now, request)
        self._emit_event("session_created", session, request)
        
        return session
    
    async def _load_existing(self, session_id: SessionID, now: datetime, request: Request | None = None) -> Session | None:
        """
        Load existing session from store and validate.
        
        Raises:
            SessionExpiredFault, SessionIdleTimeoutFault, SessionAbsoluteTimeoutFault,
            SessionFingerprintMismatchFault
        """
        try:
            session = await self.store.load(session_id)
        except SessionStoreUnavailableFault:
            self.logger.error("Session store unavailable, creating new session")
            return None
        
        if not session:
            return None
        
        # Phase 3: Validation
        is_valid, reason = self.policy.is_valid(session, now)
        
        if not is_valid:
            if reason == "expired":
                raise SessionExpiredFault(
                    session_id=str(session_id),
                    expires_at=session.expires_at.isoformat() if session.expires_at else None,
                )
            elif reason == "idle_timeout":
                raise SessionIdleTimeoutFault()
            elif reason == "absolute_timeout":
                raise SessionAbsoluteTimeoutFault()
        
        # Fingerprint verification (OWASP hijack detection)
        if self.policy.fingerprint_binding and request:
            client_ip = ""
            user_agent = ""
            if hasattr(request, 'client') and request.client:
                client_ip = request.client[0]
            if hasattr(request, 'header'):
                user_agent = request.header("user-agent") or ""
            
            if not session.verify_fingerprint(client_ip, user_agent):
                raise SessionFingerprintMismatchFault(session_id=str(session_id))
        
        # Touch session (update last_accessed_at)
        session.touch(now)
        
        return session
    
    async def _create_new(self, now: datetime, request: Request | None = None) -> Session:
        """Create new session."""
        scope = SessionScope(self.policy.scope)
        
        session = Session(
            id=SessionID(),
            created_at=now,
            last_accessed_at=now,
            expires_at=self.policy.calculate_expiry(now),
            scope=scope,
            flags=set(),
        )
        
        if self.policy.ttl and not self.policy.rotate_on_use:
            session.flags.add(SessionFlag.RENEWABLE)
        
        if not self.policy.should_persist(session):
            session.flags.add(SessionFlag.EPHEMERAL)
        
        session._policy_name = self.policy.name
        
        # Bind fingerprint if policy requires it (OWASP)
        if self.policy.fingerprint_binding and request:
            client_ip = ""
            user_agent = ""
            if hasattr(request, 'client') and request.client:
                client_ip = request.client[0]
            if hasattr(request, 'header'):
                user_agent = request.header("user-agent") or ""
            session.bind_fingerprint(client_ip, user_agent)
        
        return session
    
    # ========================================================================
    # Phase 6: Commit
    # ========================================================================
    
    async def commit(
        self,
        session: Session,
        response: Response,
        privilege_changed: bool = False,
    ) -> None:
        """
        Commit session changes (Phase 6-7: Commit, Emission).
        
        FIX: Concurrency check happens BEFORE save (not after).
        """
        now = datetime.now(timezone.utc)
        
        # Check if rotation needed
        if self.policy.should_rotate(session, privilege_changed):
            try:
                session = await self._rotate_session(session, now)
                self._emit_event("session_rotated", session, None)
            except Exception as e:
                self.logger.error(f"Session rotation failed: {e}")
                raise SessionRotationFailedFault(
                    old_id=str(session.id),
                    new_id="unknown",
                    cause=str(e),
                )
        
        # FIX: Check concurrency BEFORE save (was after save in original)
        if privilege_changed and session.is_authenticated:
            await self.check_concurrency(session)
        
        # Persist if needed
        if self.policy.should_persist(session) and session.is_dirty:
            try:
                await self.store.save(session)
                self._emit_event("session_committed", session, None)
            except SessionStoreUnavailableFault as e:
                self.logger.error(f"Failed to persist session: {e}")
        
        # Phase 7: Emission
        self.transport.inject(response, session)
    
    async def _rotate_session(self, session: Session, now: datetime) -> Session:
        """Rotate session ID (create new ID, keep data)."""
        old_id = session.id
        
        new_session = Session(
            id=SessionID(),
            principal=session.principal,
            data=session.data.copy(),
            created_at=session.created_at,
            last_accessed_at=now,
            expires_at=session.expires_at,
            scope=session.scope,
            flags=session.flags.copy(),
            version=session.version + 1,
        )
        new_session._policy_name = session._policy_name
        
        # Preserve fingerprint across rotation
        if hasattr(session, '_fingerprint') and session._fingerprint:
            object.__setattr__(new_session, '_fingerprint', session._fingerprint)
        
        new_session.mark_dirty()
        
        try:
            await self.store.delete(old_id)
        except Exception as e:
            self.logger.warning(f"Failed to delete old session: {e}")
        
        return new_session
    
    # ========================================================================
    # Session Operations
    # ========================================================================
    
    async def destroy(self, session: Session, response: Response) -> None:
        """Destroy session (logout)."""
        try:
            await self.store.delete(session.id)
            self._emit_event("session_destroyed", session, None)
        except Exception as e:
            self.logger.error(f"Failed to destroy session: {e}")
        
        self.transport.clear(response)
    
    async def check_concurrency(self, session: Session) -> None:
        """Check concurrency limits for session's principal."""
        if not session.principal:
            return
        
        if not self.policy.concurrency.max_sessions_per_principal:
            return
        
        active_count = await self.store.count_by_principal(session.principal.id)
        
        if self.policy.concurrency.violated(session.principal, active_count):
            if self.policy.concurrency.should_reject():
                raise SessionConcurrencyViolationFault(
                    principal_id=session.principal.id,
                    active_count=active_count,
                    max_allowed=self.policy.concurrency.max_sessions_per_principal,
                )
            
            elif self.policy.concurrency.should_evict_oldest():
                sessions = await self.store.list_by_principal(session.principal.id)
                if sessions:
                    oldest = min(sessions, key=lambda s: s.last_accessed_at)
                    await self.store.delete(oldest.id)
                    self.logger.info(f"Evicted oldest session for principal {session.principal.id}")
            
            elif self.policy.concurrency.should_evict_all():
                sessions = await self.store.list_by_principal(session.principal.id)
                for s in sessions:
                    if s.id != session.id:
                        await self.store.delete(s.id)
                self.logger.info(f"Evicted all sessions for principal {session.principal.id}")
    
    async def refresh(self, session: Session, now: datetime | None = None) -> None:
        """Refresh session expiry (extend TTL)."""
        if now is None:
            now = datetime.now(timezone.utc)
        
        if SessionFlag.RENEWABLE in session.flags and self.policy.ttl:
            session.extend_expiry(self.policy.ttl, now)
            self._emit_event("session_refreshed", session, None)
    
    # ========================================================================
    # Observability
    # ========================================================================
    
    def _emit_event(
        self,
        event_name: str,
        session: Session | None,
        request: Request | None,
    ) -> None:
        """Emit session event for observability."""
        event_data = {
            "event": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy": self.policy.name,
        }
        
        if session:
            event_data.update({
                "session_id_hash": session.id.fingerprint(),
                "scope": session.scope.value,
                "authenticated": session.is_authenticated,
            })
            
            if session.principal:
                event_data["principal"] = {
                    "kind": session.principal.kind,
                    "id": session.principal.id,
                }
        
        if request:
            event_data.update({
                "request_path": request.path,
                "request_method": request.method,
            })
            
            if hasattr(request, 'client') and request.client:
                event_data["client_ip"] = request.client[0]
        
        for handler in self._event_handlers:
            try:
                handler(event_data)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")
    
    def on_event(self, handler: callable) -> None:
        """Register event handler for observability."""
        self._event_handlers.append(handler)
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    async def cleanup_expired(self) -> int:
        """Remove expired sessions from store."""
        try:
            count = await self.store.cleanup_expired()
            self.logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return 0
    
    async def shutdown(self) -> None:
        """Gracefully shutdown engine."""
        await self.store.shutdown()
