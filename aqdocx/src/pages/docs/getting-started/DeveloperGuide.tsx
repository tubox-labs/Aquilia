import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { Blocks, ArrowLeft, ArrowRight, Plug, Layers, Database, Shield, Gauge, HardDrive } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DeveloperGuidePage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const subtleBorder = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Blocks className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Developer Integration Guide
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Connecting DI, Controllers, Blueprints, Models, Storage, and Cache</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${textMuted}`}>
          This guide provides a comprehensive developer walkthrough on how to wire the entire Aquilia ecosystem together. You will learn how to build a production-ready application using <DocTerm id="di.service">Dependency Injection</DocTerm>, <DocTerm id="controller.controller">Controllers</DocTerm>, validation <DocTerm id="bp.blueprint">Blueprints</DocTerm>, ORM <DocTerm id="orm.model">Models</DocTerm>, unified <DocTerm id="storage.StorageBackend">Storage</DocTerm>, and async <DocTerm id="cache.CacheService">Cache</DocTerm>.
        </p>
      </div>

      {/* Dependency Injection & Services */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Plug className="w-5 h-5 text-aquilia-500" />
          1. Dependency Injection & Service Scopes
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          Services are registered using the <DocTerm id="di.service">@service</DocTerm> decorator. You can specify whether a service is an app-scoped singleton (<code className="text-aquilia-400">scope="app"</code>) or request-scoped (<code className="text-aquilia-400">scope="request"</code>). Injected dependencies are resolved automatically via signature type annotations.
        </p>

        <CodeBlock
          language="python"
          filename="services.py"
          highlightLines={[7, 13]}
        >{`from aquilia.di import service
from aquilia.cache import CacheService
from aquilia.storage import StorageBackend

# Registered as a singleton across the entire application
@service(scope="app")
class ProductCatalogService:
    def __init__(self, cache: CacheService, storage: StorageBackend):
        self.cache = cache
        self.storage = storage

# Registered once per request, disposed automatically
@service(scope="request")
class UserContext:
    def __init__(self, token: str | None = None):
        self.token = token
        self.user = None
`}</CodeBlock>
      </section>

      {/* Blueprints & Validation */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-500" />
          2. Blueprints: Schema & Input Validation
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          A <DocTerm id="bp.blueprint">Blueprint</DocTerm> acts as a model-world contract. It handles validation, type coercion, and sanitization of incoming requests. Use the <DocTerm id="bp.ward">@ward</DocTerm> decorator for custom cross-field constraints.
        </p>

        <CodeBlock
          language="python"
          filename="blueprints.py"
          highlightLines={[5, 11]}
        >{`from aquilia.blueprints import Blueprint, Field, ward

class UserRegistrationBlueprint(Blueprint):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8)
    password_confirm: str = Field()
    username: str = Field(min_length=3, max_length=50)

    # Custom cross-field validation rule
    @ward
    def validate_password_match(self) -> None:
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
`}</CodeBlock>
      </section>

      {/* Models & Database Operations */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-500" />
          3. Models: Database & Transactions
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          Database models inherit from the base <DocTerm id="orm.model">Model</DocTerm> class. Use <DocTerm id="orm.atomic">@atomic</DocTerm> contexts to wrap multiple queries inside database transactions, guaranteeing atomic commit/rollback behavior.
        </p>

        <CodeBlock
          language="python"
          filename="models.py"
          highlightLines={[4, 11]}
        >{`from aquilia.db import Model, Field
from aquilia.db.transactions import atomic

class User(Model):
    id = Field(primary_key=True)
    username = Field(unique=True)
    email = Field(unique=True)
    password_hash = Field()
    avatar_url = Field(null=True)

@atomic
async def register_new_user(user_data: dict, password_hash: str) -> User:
    user = await User.objects.create(
        username=user_data["username"],
        email=user_data["email"],
        password_hash=password_hash
    )
    return user
`}</CodeBlock>
      </section>

      {/* Storage and Cache Integration */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <HardDrive className="w-5 h-5 text-aquilia-500" />
          4. Storage & Cache Integration
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          Use the <DocTerm id="storage.StorageBackend">StorageBackend</DocTerm> to save file uploads, and wrap operations in <DocTerm id="cache.CacheService">CacheService</DocTerm> methods or decorators (such as <DocTerm id="cache.cached">@cached</DocTerm> or <DocTerm id="cache.invalidate">@invalidate</DocTerm>) to improve read performance.
        </p>

        <CodeBlock
          language="python"
          filename="storage_cache.py"
          highlightLines={[7, 13]}
        >{`from aquilia.cache import cached, invalidate
from aquilia.storage import StorageBackend

class UserAvatarService:
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def upload_avatar(self, user_id: int, file_content: bytes) -> str:
        filename = f"avatars/{user_id}.png"
        await self.storage.save(filename, file_content)
        return self.storage.url(filename)

# Declaratively cache user profile reads for 5 minutes
@cached(ttl=300, namespace="profiles")
async def get_user_profile(user_id: int):
    return await User.objects.get(id=user_id)
`}</CodeBlock>
      </section>

      {/* Controllers: Putting It All Together */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          5. Full Stack Controller Integration
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          Controllers orchestrate the inbound request, invoke validation blueprint schema mapping, execute transactions, save uploads, and cache responses.
        </p>

        <CodeBlock
          language="python"
          filename="controllers.py"
          highlightLines={[12, 17, 23]}
        >{`from aquilia import Controller, GET, POST
from aquilia.controller import RequestCtx
from aquilia.http import Response
from aquilia.cache import CacheService
from aquilia.storage import StorageBackend
from .blueprints import UserRegistrationBlueprint
from .models import User, register_new_user

class UserRegistrationController(Controller):
    prefix = "/users"

    def __init__(self, cache: CacheService, storage: StorageBackend):
        self.cache = cache
        self.storage = storage

    @POST("/register")
    async def register(self, ctx: RequestCtx):
        # Bind payload to blueprint contract
        blueprint = await ctx.bind(UserRegistrationBlueprint)
        
        # Safe database write
        password_hash = hash_password(blueprint.password)
        user = await register_new_user(blueprint.to_dict(), password_hash)

        # Invalidate related profile caches
        await self.cache.delete(f"profile:{user.id}", namespace="profiles")

        return Response.json(user.to_dict(), status=201)

    @GET("/{user_id}/avatar")
    async def get_avatar(self, ctx: RequestCtx, user_id: int):
        # Retrieve cached profile or read from database
        avatar_url = await self.cache.get_or_set(
            key=f"avatar:{user_id}",
            loader=lambda: self._fetch_avatar_url(user_id),
            ttl=600,
            namespace="profiles"
        )
        return Response.json({"avatar_url": avatar_url})

    async def _fetch_avatar_url(self, user_id: int) -> str:
        user = await User.objects.get(id=user_id)
        return user.avatar_url or "https://avatars.example.com/default.png"
`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${subtleBorder}`}>
        <Link to="/docs/quickstart" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Quick Start
        </Link>
        <Link to="/docs/architecture" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Architecture <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Architecture Diagram', link: '/docs/architecture' },
          { text: 'Dependency Injection Details', link: '/docs/di' },
          { text: 'ORM Models & Fields', link: '/docs/models/overview' },
          { text: 'Validation Blueprints', link: '/docs/blueprints/overview' },
        ]}
      />
    </div>
  )
}
