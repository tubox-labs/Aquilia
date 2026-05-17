from __future__ import annotations

from aquilia.auth.core import Identity, IdentityType, PasswordCredential
from aquilia.auth.hashing import PasswordHasher
from aquilia.auth.manager import AuthManager
from aquilia.auth.stores import MemoryCredentialStore, MemoryIdentityStore, MemoryTokenStore
from aquilia.auth.tokens import KeyDescriptor, KeyRing, TokenManager
from aquilia.faults import ConflictFault, NotFoundFault
from aquilia.sessions import SessionScope


class AccountsService:
    def __init__(self):
        self.identity_store = MemoryIdentityStore()
        self.credential_store = MemoryCredentialStore()
        self.token_store = MemoryTokenStore()
        self.password_hasher = PasswordHasher()
        key = KeyDescriptor.generate(kid="auth-starter-dev", algorithm="HS256", secret="replace-in-production")
        self.token_manager = TokenManager(key_ring=KeyRing(keys=[key]), token_store=self.token_store)
        self.manager = AuthManager(
            token_manager=self.token_manager,
            identity_store=self.identity_store,
            credential_store=self.credential_store,
            password_hasher=self.password_hasher,
        )

    async def register(self, data: dict):
        email = data["email"]
        existing = await self.identity_store.get_by_attribute("email", email)
        if existing:
            raise ConflictFault(detail="An account with that email already exists")
        identity = Identity(
            id=f"usr_{email.split('@')[0].replace('.', '_')}",
            type=IdentityType.USER,
            attributes={"email": email, "name": data["name"], "roles": ["member"], "email_verified": False},
        )
        await self.identity_store.create(identity)
        await self.credential_store.save_password(
            PasswordCredential(identity_id=identity.id, password_hash=self.password_hasher.hash(data["password"]))
        )
        return identity.to_dict()

    async def login(self, data: dict):
        result = await self.manager.sign_in(
            username=data["email"],
            password=data["password"],
            scopes=SessionScope.USER,
            session="new",
        )
        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": "Bearer",
            "identity": result.identity.to_dict(),
            "session_id": result.session_id,
        }

    async def get_identity(self, identity_id: str):
        identity = await self.identity_store.get(identity_id)
        if identity is None:
            raise NotFoundFault(detail="Identity was not found")
        return identity.to_dict()
