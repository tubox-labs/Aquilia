import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { Blocks, ArrowLeft, ArrowRight, Plug, Layers, Database, Shield } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DeveloperGuidePage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const subtleBorder = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Blocks className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="gradient-text font-mono">Developer Integration Guide</span>
            </h1>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} font-mono mt-1`}>
              Connecting DI, Controllers, Blueprints, Models, Storage, Cache, and Mail
            </p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${textMuted}`}>
          This guide outlines how to build a unified application flow in Aquilia. You will learn how to connect <DocTerm id="di.service">Dependency Injection</DocTerm>, HTTP <DocTerm id="controller.controller">Controllers</DocTerm>, validation <DocTerm id="bp.blueprint">Blueprints</DocTerm>, ORM <DocTerm id="orm.model">Models</DocTerm>, <DocTerm id="storage.StorageBackend">Storage</DocTerm>, <DocTerm id="cache.CacheService">Cache</DocTerm>, and <DocTerm id="mail.MailService">Mail</DocTerm> in a single cohesive codebase.
        </p>
      </div>

      {/* Dependency Injection & Services */}
      <section className="mb-16 border-l border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Plug className="w-5 h-5 text-aquilia-500" />
          1. Dependency Injection & Service Scopes
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          Mark classes as services using the <DocTerm id="di.service">@service</DocTerm> decorator. Constructor parameters are automatically autowired by the container using type hints:
        </p>

        <CodeBlock
          language="python"
          filename="services.py"
          highlightLines={[6, 12, 13]}
        >{`from aquilia.di import service
from aquilia.cache import CacheService
from aquilia.storage import StorageBackend

# 1. Registered as a singleton across the entire app scope
@service(scope="app")
class ProductCatalogService:
    def __init__(self, cache: CacheService, storage: StorageBackend):
        self.cache = cache
        self.storage = storage

# 2. Registered once per HTTP request scope and disposed on request end
@service(scope="request")
class UserContext:
    def __init__(self):
        self.user = None
`}</CodeBlock>
      </section>

      {/* Blueprints & Validation */}
      <section className="mb-16 border-l border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-500" />
          2. Blueprints: Schema & Input Validation
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          A <DocTerm id="bp.blueprint">Blueprint</DocTerm> defines request data validation schemas. Use the <DocTerm id="bp.ward">@ward</DocTerm> decorator to implement custom cross-field constraints:
        </p>

        <CodeBlock
          language="python"
          filename="blueprints.py"
          highlightLines={[3, 9, 10]}
        >{`from aquilia.blueprints import Blueprint, Field, ward

class UserRegistrationBlueprint(Blueprint):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8)
    password_confirm: str = Field()
    username: str = Field(min_length=3, max_length=50)

    @ward
    def validate_password_match(self) -> None:
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
`}</CodeBlock>
      </section>

      {/* Models & Database Operations */}
      <section className="mb-16 border-l border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-500" />
          3. Models: Database & Transactions
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          Database models inherit from the base <DocTerm id="orm.model">Model</DocTerm> class. Wrap multiple queries inside <DocTerm id="orm.atomic">atomic()</DocTerm> async context managers to execute database transactions:
        </p>

        <CodeBlock
          language="python"
          filename="models.py"
          highlightLines={[1, 4, 11]}
        >{`from aquilia.models import Model, CharField, AutoField, atomic

class User(Model):
    id = AutoField(primary_key=True)
    username = CharField(unique=True, max_length=50)
    email = CharField(unique=True, max_length=255)
    password_hash = CharField(max_length=255)
    avatar_url = CharField(null=True, max_length=512)

async def create_user_transaction(user_data: dict, password_hash: str) -> User:
    # Executes queries inside a database transaction block
    async with atomic():
        user = await User.objects.create(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=password_hash
        )
        return user
`}</CodeBlock>
      </section>

      {/* Put It All Together: Orchestrated Controller */}
      <section className="mb-16 border-l border-aquilia-500/30 pl-6 py-1">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          4. Putting It All Together: The Unified Controller
        </h2>
        <p className={`mb-4 ${textMuted}`}>
          Here is how to orchestrate a complete flow inside an HTTP <DocTerm id="controller.controller">Controller</DocTerm>. The endpoint binds schema blueprints, saves files to <DocTerm id="storage.StorageBackend">StorageBackend</DocTerm>, writes transaction records, invalidates related <DocTerm id="cache.CacheService">CacheService</DocTerm> entries, and dispatches custom <DocTerm id="mail.TemplateMessage">TemplateMessage</DocTerm> emails:
        </p>

        <CodeBlock
          language="python"
          filename="registration_controller.py"
          highlightLines={[14, 19, 21, 28, 31, 34]}
        >{`from aquilia import Controller, POST
from aquilia.controller import RequestCtx
from aquilia.http import Response
from aquilia.cache import CacheService
from aquilia.storage import StorageBackend
from aquilia.mail import TemplateMessage
from .blueprints import UserRegistrationBlueprint
from .models import User, create_user_transaction

class RegistrationController(Controller):
    prefix = "/users"

    # Dependency Injection automatically wires service parameters
    def __init__(self, cache: CacheService, storage: StorageBackend):
        self.cache = cache
        self.storage = storage

    @POST("/register")
    async def register(self, ctx: RequestCtx):
        # 1. Bind and validate request body against Blueprint schema contract
        blueprint = await ctx.bind(UserRegistrationBlueprint)
        
        # 2. Process file uploads via Storage
        avatar_file = ctx.request.files.get("avatar")
        avatar_url = None
        if avatar_file:
            filename = f"avatars/{blueprint.username}.png"
            await self.storage.save(filename, avatar_file.read())
            avatar_url = self.storage.url(filename)

        # 3. Write data inside a database transaction
        user = await create_user_transaction(blueprint.to_dict(), "hashed_pw")
        if avatar_url:
            user.avatar_url = avatar_url
            await user.save()

        # 4. Invalidate related cache tags
        await self.cache.delete("catalog:count")

        # 5. Dispatch template confirmation email
        msg = TemplateMessage(
            template="welcome.aqt",
            context={"username": user.username},
            subject="Welcome, << username >>!",
            to=[user.email]
        )
        await msg.asend()

        return Response.json(user.to_dict(), status=201)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${subtleBorder}`}>
        <Link to="/docs/getting-started/quickstart" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Quick Start
        </Link>
        <Link to="/docs/getting-started/introduction" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Introduction <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Dependency Injection Details', link: '/docs/di' },
          { text: 'ORM Models & Fields', link: '/docs/models/overview' },
          { text: 'Validation Blueprints', link: '/docs/blueprints/overview' },
          { text: 'Unified File Storage', link: '/docs/storage' },
        ]}
      />
    </div>
  )
}
