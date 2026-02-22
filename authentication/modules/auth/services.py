"""
Auth module services (business logic).

Services contain the core business logic and are auto-wired
via dependency injection.
"""

from typing import Optional, List
from aquilia.di import service

from .serializer import RegisterInputModel
from .faults import AuthOperationFault
from .models.models import UsersModel
from aquilia.auth import (
    AuthManager,
    PasswordHasher, 
    Identity, 
    PasswordCredential, 
    IdentityType,
    IdentityStatus
)

@service(scope="app")
class AuthService:
    """
    Service for auth business logic.

    This service is automatically registered with the DI container
    and can be injected into controllers.

    To inject dependencies, add type-annotated parameters to __init__:

        def __init__(self, db: AquiliaDatabase, auth: AuthManager):
            self.db = db
            self.auth = auth
    """

    def __init__(self, auth: AuthManager, hasher: PasswordHasher):
        self.auth = auth
        self.hasher = hasher

    async def register(self, data: RegisterInputModel):
        password_hash = self.hasher.hash(data.password)

        if await UsersModel.query().filter(email = data.email).exists():
            raise AuthOperationFault("user.register", f"Email: {data.email} already exisits!")

        user = await UsersModel.create(
            username = data.username,
            email = data.email,
            password = password_hash,
            name = data.name
        )
        identity = Identity(
            id = str(user.id),
            type = IdentityType.USER,
            status = IdentityStatus.ACTIVE,
            attributes = {
                "username": data.username,
                "email": data.email,
                "name": data.name
            }
        )
        
        await self.auth.identity_store.create(identity = identity)

        credential = PasswordCredential(
            identity_id = str(user.id),
            password_hash = password_hash
        )

        await self.auth.credential_store.save_password(credential = credential)
        return user