import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import {
  BookOpen,
  Terminal,
  Settings,
  Database,
  Shield,
  Tag,
  Play,
  CheckCircle,
} from 'lucide-react'

export function AuthTutorialPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [activeStep, setActiveStep] = useState(1)

  const steps = [
    { id: 1, title: 'Architecture', icon: <BookOpen className="w-4 h-4" /> },
    { id: 2, title: 'User Model', icon: <Database className="w-4 h-4" /> },
    { id: 3, title: 'Contracts', icon: <Tag className="w-4 h-4" /> },
    { id: 4, title: 'Auth Faults', icon: <Shield className="w-4 h-4" /> },
    { id: 5, title: 'UserService', icon: <Settings className="w-4 h-4" /> },
    { id: 6, title: 'Controller', icon: <Terminal className="w-4 h-4" /> },
    { id: 7, title: 'Wiring Up', icon: <Play className="w-4 h-4" /> },
    { id: 8, title: 'Smoke Tests', icon: <CheckCircle className="w-4 h-4" /> },
  ]

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Shield className="w-4 h-4" />
          Tutorials / End-to-End Auth App
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Authentication Application
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Learn how to build a complete, production-grade Authentication and Session flow in Aquilia.
          We will implement user registration, Argon2id password hashing, session lifecycle management, login/logout endpoints, and a guarded profile route.
        </p>
      </div>

      {/* Horizontal Steps Stepper (Connecting nodes, no line crossover) */}
      <div className="relative mb-16 flex justify-between items-center max-w-3xl mx-auto px-4">
        {/* Track Line (positioned absolute left-0 right-0, covered by opaque bubbles) */}
        <div className={`absolute top-[20px] left-0 right-0 h-[2px] -translate-y-1/2 ${isDark ? 'bg-white/10' : 'bg-gray-200'} z-0`} />
        
        {/* Active Line Highlight */}
        <div 
          className="absolute top-[20px] left-0 h-[2px] -translate-y-1/2 bg-gradient-to-r from-aquilia-500 to-aquilia-400 transition-all duration-300 z-0" 
          style={{ width: `${((activeStep - 1) / (steps.length - 1)) * 100}%` }}
        />

        {steps.map((step) => {
          const isActive = activeStep === step.id
          const isCompleted = activeStep > step.id

          return (
            <button
              key={step.id}
              onClick={() => setActiveStep(step.id)}
              className="relative flex flex-col items-center focus:outline-none cursor-pointer group z-10"
            >
              {/* Opaque node bubbles that block the track line from crossing over */}
              <div 
                className={`w-10 h-10 rounded-full flex items-center justify-center border transition-all duration-300 ${
                  isActive 
                    ? 'bg-aquilia-500 border-aquilia-400 text-white shadow-lg shadow-aquilia-500/20 scale-110' 
                    : isCompleted
                      ? isDark 
                        ? 'bg-zinc-900 border-aquilia-500 text-aquilia-400' 
                        : 'bg-emerald-50 border-aquilia-500 text-aquilia-500'
                      : isDark
                        ? 'bg-zinc-950 border-zinc-800 text-zinc-500 hover:border-zinc-700'
                        : 'bg-white border-gray-200 text-gray-400 hover:border-gray-400'
                }`}
              >
                {step.icon}
              </div>
              <span 
                className={`absolute top-12 text-xs font-mono hidden md:inline transition-all duration-200 whitespace-nowrap ${
                  isActive 
                    ? 'text-aquilia-500 font-bold' 
                    : 'text-zinc-500 group-hover:text-zinc-400'
                }`}
              >
                {step.title}
              </span>
            </button>
          )
        })}
      </div>

      {/* Step Content Container */}
      <div className={`min-h-[400px] border-b pb-8 ${isDark ? 'border-white/5' : 'border-zinc-100'}`}>
        <AnimatePresence mode="wait">
          {activeStep === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 1: Auth Architecture & CLI Scaffolding</h3>
              <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Aquilia includes a secure, built-in identity management system called <strong className="text-aquilia-400">AquilAuth</strong>.
                Unlike frameworks that require third-party libraries for auth, Aquilia ships with native support for password verification, session tracking, and role-based guards.
              </p>

              <h4 className={`text-md font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Interactive Command to Add Module</h4>
              <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                To add the module interactively (allowing you to step through setup questions in the terminal):
              </p>
              <CodeBlock
                code={`aq add module`}
                language="bash"
              />

              <h4 className={`text-md font-bold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Non-Interactive Command to Add Module</h4>
              <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Alternatively, to skip all questions and generate the boilerplate files instantly in one command:
              </p>
              <CodeBlock
                code={`aq add module auth --route-prefix=/auth -y`}
                language="bash"
              />

              <h4 className={`text-md font-bold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Components of the Flow:</h4>
              <ul className={`space-y-4 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span>
                    <strong className={isDark ? 'text-white' : 'text-gray-955'}>Password Hashing:</strong> Powered by the <code className="text-aquilia-400">PasswordHasher</code> class, which uses cryptographically strong algorithms (Argon2id or Bcrypt) out of the box.
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span>
                    <strong className={isDark ? 'text-white' : 'text-gray-955'}>Session Principal Binding:</strong> Authenticated sessions bind to a <code className="text-aquilia-400">SessionPrincipal</code>. This binds the user ID and permissions to the connection context.
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span>
                    <strong className={isDark ? 'text-white' : 'text-gray-955'}>Identity Context Injection:</strong> If a session carries an active principal, Aquilia's <code className="text-aquilia-400">SessionAuthBridge</code> automatically instantiates an <DocTerm id="auth.identity">Identity</DocTerm> object and injects it directly into protected route handlers.
                  </span>
                </li>
              </ul>
            </motion.div>
          )}

          {activeStep === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 2: Database Models, Constraints & Indexes</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Let's create the database schema. We'll define a <code className="text-aquilia-400">User</code> model to store user credentials, using custom indexes and check constraints.
                Open <code className="text-aquilia-400">modules/auth/models.py</code>:
              </p>

              <CodeBlock
                code={`# modules/auth/models.py
from datetime import datetime
from aquilia.database import Model
from aquilia.models import fields
from aquilia.models import Index, UniqueConstraint


class User(Model):
    """
    SQL database model representing a registered user account.
    """
    id = fields.IntegerField(primary_key=True)
    username = fields.CharField(max_length=150, unique=True, index=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    last_login = fields.DateTimeField(null=True)

    class Meta:
        table_name = "auth_users"
        # Custom composite index for fast credential checks
        indexes = [
            Index(fields=["username", "is_active"], name="idx_users_username_active")
        ]
        # Multi-column unique constraints
        constraints = [
            UniqueConstraint(fields=["username", "email"], name="uq_user_credentials")
        ]
`}
                language="python"
                filename="models.py"
                highlightLines={[5, 20, 22, 24, 26]}
              />

              {/* Callouts */}
              <div className="space-y-4 mt-6">
                <div className={`p-4 border-l-4 border-aquilia-500 ${isDark ? 'bg-zinc-900/50' : 'bg-gray-50'}`}>
                  <h5 className={`text-sm font-bold flex items-center gap-1.5 ${isDark ? 'text-white' : 'text-gray-955'}`}>
                    <Shield className="w-4 h-4 text-aquilia-500" />
                    How Index Works in Meta
                  </h5>
                  <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    The <code className="text-aquilia-400">Index(fields=["username", "is_active"])</code> creates a composite index.
                    In production, this ensures queries checking if a username is active run in log(N) time instead of checking every table row.
                  </p>
                </div>

                <div className={`p-4 border-l-4 border-yellow-500 ${isDark ? 'bg-zinc-900/50' : 'bg-gray-50'}`}>
                  <h5 className={`text-sm font-bold flex items-center gap-1.5 ${isDark ? 'text-white' : 'text-gray-955'}`}>
                    <Shield className="w-4 h-4 text-yellow-500" />
                    UniqueConstraint Advantage
                  </h5>
                  <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Declaring a <code className="text-aquilia-400">UniqueConstraint</code> on `username` and `email` ensures duplicates cannot be inserted due to racing API requests. This pushes integrity enforcement directly into the SQL engine.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeStep === 3 && (
            <motion.div
              key="step-3"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 3: Creating Validation Contracts & Wards</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/auth/contracts.py</code>. We will define schemas to validate register and login requests.
                We will showcase Aquilia's validation transforms (<code className="text-aquilia-400">{" >> "}</code> shift composition operator) to clean inputs:
              </p>

              {/* Stacked Contract definition styles */}
              <div className="space-y-6 my-6">
                <div>
                  <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Option A: Explicit Facet Descriptors</h4>
                  <p className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Uses explicit <DocTerm id="bp.facet">Facet</DocTerm> class descriptors:
                  </p>
                  <CodeBlock
                    code={`from aquilia import Contract
from aquilia.contracts import Facet

class RegisterContract(Contract):
    username = Facet.text(min_length=3, max_length=150)
    email = Facet.email()
    password = Facet.text(min_length=8)

    class Spec:
        extra_fields = "reject"
`}
                    language="python"
                  />
                </div>

                <div>
                  <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Option B: Type-Annotated Fields with Wards (Modern Hashing Way)</h4>
                  <p className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Modern style using type annotations, validation pipelines, and an async <DocTerm id="bp.ward">@ward</DocTerm> method to automatically hash passwords inside the contract itself:
                  </p>
                  <CodeBlock
                    code={`from typing import Annotated
from aquilia import Contract, Field
from aquilia.contracts import Facet, ward
from aquilia.contracts.transforms import strip, lower, slugify
from aquilia.auth import PasswordHasher, PasswordPolicy

EmailType = Annotated[str, Facet.email() >> strip >> lower]
SlugType = Annotated[str, Facet.text() >> strip >> lower >> slugify]

class RegisterContract(Contract):
    username: SlugType = Field(min_length=3)
    email: EmailType = Field()
    password: str = Field(min_length=8)

    class Spec:
        model = User
        fields = ["username", "email"]  # Writable fields for imprinting
        extra_fields = "reject"

    @ward(mode="async")
    async def validate_and_hash_password(self, data: dict):
        password = data.get("password")
        if not password:
            self.reject("password", "Password is required")
            return data

        # Enforce password strength policy
        policy = PasswordPolicy(min_length=8)
        is_valid, errors = await policy.validate_async(password=password)
        if not is_valid:
            self.reject("password", errors)

        # Hash and inject the password_hash directly into validation data dictionary
        hasher = PasswordHasher()
        password_hash = await hasher.hash_async(password=password)
        self.data["password_hash"] = password_hash
        return data
`}
                    language="python"
                  />
                </div>
              </div>

              <h4 className={`text-md font-bold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Inbound & Outbound Contracts:</h4>
              <CodeBlock
                code={`# modules/auth/contracts.py
from datetime import datetime
from typing import Annotated
from aquilia import Contract, Field
from aquilia.contracts import Facet
from aquilia.contracts.transforms import strip, lower, slugify
from .models import User

EmailType = Annotated[str, Facet.email() >> strip >> lower]
SlugType = Annotated[str, Facet.text() >> strip >> lower >> slugify]


class LoginContract(Contract):
    """
    Schema for validating sign-in requests.
    """
    username: str = Field(min_length=3)
    password: str = Field(min_length=1)

    class Spec:
        extra_fields = "reject"


class UserResponseContract(Contract):
    """
    Schema for serializing outbound user statistics (masking secrets).
    """
    id: int = Field(read_only=True)
    username: str = Field(read_only=True)
    email: str = Field(read_only=True)
    created_at: datetime = Field(read_only=True)

    class Spec:
        model = User
        fields = ["id", "username", "email", "created_at"]


class LoginResponseContract(Contract):
    """
    Outbound response contract after a successful sign-in.
    """
    access_token: str = Field()
    refresh_token: str = Field()
    message: str = Field()
    user: UserResponseContract = Field()  # Nested schema
`}
                language="python"
                filename="contracts.py"
                highlightLines={[12, 23, 38]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Understanding Spec Configurations & Methods:</h4>
              <ul className={`space-y-3.5 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>model:</strong> Links the contract schema to a database model class.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>fields:</strong> Filters which model fields should be parsed or serialized. Set to <code className="text-aquilia-400">"__all__"</code> to include all fields.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>exclude:</strong> Excludes specified fields (e.g. secret hash keys) from serialization outputs.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>read_only_fields / write_only_fields:</strong> Sets unidirectional permissions on properties.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>is_sealed():</strong> Evaluates if a contract validation is run successfully.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>imprint():</strong> Resolves and saves validated data directly to the database model.</span>
                </li>
              </ul>
            </motion.div>
          )}

          {activeStep === 4 && (
            <motion.div
              key="step-4"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 4: Creating Authentication Faults</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/auth/faults.py</code>. We define specialized domain faults for registration conflicts.
              </p>

              <CodeBlock
                code={`# modules/auth/faults.py
from aquilia.faults import Fault, FaultDomain, Severity

AUTH_DOMAIN = FaultDomain.custom(
    "AUTH_APP",
    "Authentication application domain faults",
)


class AuthValidationFault(Fault):
    """
    Raised when validation checks (e.g. email duplication) fail.
    """
    domain = AUTH_DOMAIN
    severity = Severity.INFO
    code = "AUTH_VALIDATION_ERROR"

    def __init__(self, message: str):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=message,
            retryable=False,
            public=True,
        )
`}
                language="python"
                filename="faults.py"
                highlightLines={[10]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>The Aquilia Fault Advantage:</h4>
              <p className={`text-sm mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Unlike raw exceptions, Aquilia Faults encapsulate code mappings, severity alerts, client disclosure flags, and contextual metadata.
                When a Fault occurs, the framework's middleware converts the metadata directly into structured JSON errors, preventing database connection secrets or private tracebacks from being leaked.
              </p>
            </motion.div>
          )}

          {activeStep === 5 && (
            <motion.div
              key="step-5"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 5: UserService Hashing Options</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/auth/services.py</code>. We will write the business layer.
                We illustrate **two separate ways** of hashing passwords and handling user records:
              </p>

              {/* Way 1: Standard Service Hashing */}
              <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Way 1: Standard Service Hashing (Traditional)</h4>
              <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Accesses <code className="text-aquilia-400">user_data.password</code> directly, hashes it in the service layer using the injected <code className="text-aquilia-400">PasswordHasher</code>, and instantiates the Model manually:
              </p>
              <CodeBlock
                code={`# Way 1 snippet in modules/auth/services.py
    async def register(self, user_data: RegisterContract) -> User:
        """Traditional manual hashing and model creation."""
        existing_user = await User.query().filter(email=user_data.email).first()
        if existing_user:
            raise AuthValidationFault(f"A user with this email {user_data.email} already exists.")

        # Hash password and save manually
        hashed_pass = self.hasher.hash(user_data.password)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_pass,
        )
        await user.save()
        return user
`}
                language="python"
              />

              {/* Way 2: Modern Contract Hashing via Wards */}
              <h4 className={`text-md font-bold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Way 2: Automatic DB Imprinting with Contract @ward (Modern Way)</h4>
              <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Since password validation and hashing occurred automatically in the contract's async <DocTerm id="bp.ward">@ward</DocTerm>, the service doesn't need to manually hash anything. It simply calls <DocTerm id="bp.imprint">imprint()</DocTerm> directly:
              </p>
              <CodeBlock
                code={`# Way 2 snippet in modules/auth/services.py
    async def register_modern(self, user_data: RegisterContract) -> User:
        """Modern way -- validators and hashes are encapsulated inside the contract."""
        existing_user = await User.query().filter(email=user_data.email).first()
        if existing_user:
            raise AuthValidationFault(f"A user with this email {user_data.email} already exists.")

        # The contract automatically validated and hashed the password into 'password_hash'.
        # imprint() creates and saves the User model instance in one step.
        user = await user_data.imprint()
        return user
`}
                language="python"
              />

              <h4 className={`text-md font-bold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Complete UserService Class:</h4>
              <CodeBlock
                code={`# modules/auth/services.py
from aquilia.di import service
from aquilia.auth import PasswordHasher
from .models import User
from .contracts import RegisterContract
from .faults import AuthValidationFault


@service(scope="app")
class UserService:
    """
    UserService handles password hashing, user registration, and authentication verification.
    """
    def __init__(self, hasher: PasswordHasher):
        # Resolved and injected by Dependency Injection (DI) automatically
        self.hasher = hasher

    async def register(self, user_data: RegisterContract) -> User:
        """Register using Way 2: Modern imprint method."""
        existing_user = await User.query().filter(email=user_data.email).first()
        if existing_user:
            raise AuthValidationFault(f"A user with this email {user_data.email} already exists.")

        # Imprint does the creation and writes username, email, and password_hash
        user = await user_data.imprint()
        return user

    async def verify_credentials(self, username: str, raw_pass: str) -> User:
        """Verify username exists and matches hashed password."""
        try:
            user = await User.objects.get(username=username)
        except Exception:
            raise AuthValidationFault("Invalid credentials")

        if not user.is_active:
            raise AuthValidationFault("User account is inactive")

        # Validate password
        is_valid = self.hasher.verify(raw_pass, user.password_hash)
        if not is_valid:
            raise AuthValidationFault("Invalid credentials")

        return user
`}
                language="python"
                filename="services.py"
                highlightLines={[12, 19, 21, 25, 29, 39]}
              />
            </motion.div>
          )}

          {activeStep === 6 && (
            <motion.div
              key="step-6"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 6: Writing the Controller & AuthManager</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/auth/controllers.py</code>.
                We inject <code className="text-aquilia-400">AuthManager</code> to authenticate passwords and manage tokens.
                Notice how we return the access and refresh token inside the structured <code className="text-aquilia-400">LoginResponseContract</code>:
              </p>

              <CodeBlock
                code={`# modules/auth/controllers.py
from aquilia import Controller, POST, GET, RequestCtx, Response
from aquilia.auth import authenticated, Identity, AuthManager
from .services import UserService
from .contracts import RegisterContract, LoginContract, UserResponseContract, LoginResponseContract
from .models import User


class AuthController(Controller):
    """
    Handles register, sign-in, sign-out, and profile retrieval.
    """
    prefix = "/auth"
    tags = ["auth"]

    def __init__(self, service: UserService, auth_manager: AuthManager):
        # Resolved and injected by DI
        self.service = service
        self.auth_manager = auth_manager

    @POST("/register", request_contract=RegisterContract, response_contract=UserResponseContract)
    async def signup(self, ctx: RequestCtx, contract: RegisterContract):
        """Register a user."""
        user = await self.service.register(contract)
        return Response.json(user, status=201)

    @POST("/login", request_contract=LoginContract, response_contract=LoginResponseContract)
    async def signin(self, ctx: RequestCtx, contract: LoginContract):
        """Authenticate user and return Access and Refresh Tokens."""
        # 1. Credentials are automatically validated; access attributes directly
        user = await self.service.verify_credentials(
            contract.username,
            contract.password,
        )

        # 2. Invoke AuthManager high-level sign_in API
        auth_result = await self.auth_manager.sign_in(
            username=contract.username,
            password=contract.password,
        )

        # 3. Return response conforming to LoginResponseContract structure
        return Response.json({
            "access_token": auth_result.access_token,
            "refresh_token": auth_result.refresh_token,
            "message": "Login successful",
            "user": user,
        })

    @GET("/me", response_contract=UserResponseContract)
    @authenticated
    async def profile(self, ctx: RequestCtx, user: Identity):
        """Protected profile - identity auto-injected by @authenticated bridge."""
        db_user = await User.objects.get(id=user.id)
        return Response.json(db_user)

    @POST("/logout")
    async def signout(self, ctx: RequestCtx):
        """Sign out user and clear session cookies."""
        await self.auth_manager.sign_out()
        return Response.json({"message": "Successfully logged out"})
`}
                language="python"
                filename="controllers.py"
                highlightLines={[22, 27, 34, 40, 46, 54]}
              />
            </motion.div>
          )}

          {activeStep === 7 && (
            <motion.div
              key="step-7"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 7: Manual Wiring vs. Auto-Discovery</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                To register the auth module within the workspace, Aquilia supports both manual configuration and full auto-discovery.
              </p>

              {/* Wiring Comparison (Stacked Vertically) */}
              <div className="space-y-6 my-6">
                <div>
                  <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Manual Wiring</h4>
                  <p className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Explicitly import and register components inside <code className="text-aquilia-400">manifest.py</code>:
                  </p>
                  <CodeBlock
                    code={`# manifest.py (Manual)
manifest = AppManifest(
    name="auth",
    controllers=["modules.auth.controllers:AuthController"],
    services=["modules.auth.services:UserService"],
    models=["modules.auth.models:User"],
    auto_discover=False,
)
`}
                    language="python"
                  />
                </div>

                <div>
                  <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Auto-Discovery (Recommended)</h4>
                  <p className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Enable auto-discovery to automatically scan directory files for route declarations and DI classes:
                  </p>
                  <CodeBlock
                    code={`# manifest.py (Auto-Discovery)
manifest = AppManifest(
    name="auth",
    auto_discover=True,  # Scans and registers automatically
)
`}
                    language="python"
                  />
                </div>
              </div>

              <h4 className={`text-md font-bold mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Configure in workspace.py:</h4>
              <CodeBlock
                code={`# workspace.py
from datetime import timedelta
from aquilia import Workspace, Module
from aquilia.sessions import SessionPolicy, TransportPolicy
from aquilia.integrations import DiIntegration, DatabaseIntegration

workspace = (
    Workspace(name="auth_server")
    .env_config(BaseEnv)
    
    # 1. Register our authentication module
    .module(Module("auth", version="0.1.0").route_prefix("/api/v1"))

    # 2. Configure sessions
    .sessions(
        policies=[
            SessionPolicy(
                name="default",
                ttl=timedelta(days=7),
                rotate_on_privilege_change=True,
                transport=TransportPolicy(
                    cookie_name="aquilia_session",
                    cookie_httponly=True,
                )
            ),
        ]
    )

    .integrate(DiIntegration(auto_wire=True))
    .integrate(DatabaseIntegration(url="sqlite:///auth.db"))
)
`}
                language="python"
                filename="workspace.py"
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Verify and Migrate database:</h4>
              <CodeBlock
                code={`# 1. Generate migrations scripts for auth tables
aq db makemigrations

# 2. Execute table creation script
aq db migrate

# 3. Verify workspace dependency tree
aq validate

# 4. Boot server
aq run`}
                language="bash"
              />
            </motion.div>
          )}

          {activeStep === 8 && (
            <motion.div
              key="step-8"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 8: Outbound Testing with aquilia.http</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                To perform live integration or smoke testing against your auth application, Aquilia provides a built-in asynchronous HTTP client: <strong className="text-aquilia-400">aquilia.http</strong>.
                Below is a complete test script (`smoke_test.py`) that uses `AsyncHTTPClient` to verify the registration, login, profile, and logout flow:
              </p>

              <CodeBlock
                code={`# smoke_test.py
import asyncio
from aquilia.http import AsyncHTTPClient
from aquilia.http.config import HTTPClientConfig
from aquilia.http.faults import HTTPClientFault


async def run_smoke_test():
    # Configure the outbound HTTP client with base URL
    config = HTTPClientConfig(
        base_url="http://localhost:8000/api/v1",
        follow_redirects=True,
    )

    # AsyncHTTPClient manages connection pooling and cookie persistence automatically
    async with AsyncHTTPClient(config=config) as client:
        print("[Smoke Test] Initiating client registration check...")
        
        try:
            # 1. Register a user
            reg_res = await client.post(
                "/auth/register",
                json={
                    "username": "smoke_tester",
                    "email": "smoke_tester@site.com",
                    "password": "supersecurepassword123"
                }
            )
            print(f"-> Registration Response Status: {reg_res.status_code}")
            # .json() is an async coroutine returning the parsed dict/list
            print(f"-> Registration Output: {await reg_res.json()}")

            # 2. Log in (CookieJar automatically captures and saves session cookies)
            login_res = await client.post(
                "/auth/login",
                json={
                    "username": "smoke_tester",
                    "password": "supersecurepassword123"
                }
            )
            print(f"-> Login Response Status: {login_res.status_code}")
            login_data = await login_res.json()
            print(f"-> Access Token: {login_data.get('access_token')}")

            # 3. Request protected route (client automatically attaches the stored session cookie)
            me_res = await client.get("/auth/me")
            print(f"-> Protected Route Profile Status: {me_res.status_code}")
            print(f"-> User Profile: {await me_res.json()}")

            # 4. Log out
            logout_res = await client.post("/auth/logout")
            print(f"-> Logout Response Status: {logout_res.status_code}")
            print(f"-> Logout Message: {await logout_res.json()}")

        except HTTPClientFault as exc:
            print(f"[ERROR] HTTP outbound call failed: {exc.message} (Code: {exc.code})")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
`}
                language="python"
                filename="smoke_test.py"
                highlightLines={[10, 16, 20, 31, 41, 46, 50]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Key Features of aquilia.http AsyncHTTPClient:</h4>
              <ul className={`space-y-3.5 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>Automatic Cookie Management:</strong> Built-in <code className="text-aquilia-400">CookieJar</code> automatically parses and sends back session cookies in consecutive requests, mimicking browser behaviors perfectly.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>Connection Pooling:</strong> Managed connections allow highly performant reuse of TCP sockets under host limit locks.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-955'}>Structured Fault Domains:</strong> All outbound HTTP request exceptions map to typed `HTTPClientFault` subclasses, allowing clean error tracking and backoff handling.</span>
                </li>
              </ul>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between items-center mt-12 pt-6 border-t border-white/5">
        <button
          onClick={() => setActiveStep((prev) => Math.max(1, prev - 1))}
          disabled={activeStep === 1}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition cursor-pointer border ${
            activeStep === 1
              ? 'opacity-40 cursor-not-allowed border-transparent'
              : isDark
                ? 'text-gray-300 hover:text-white border-white/10 hover:bg-white/5'
                : 'text-gray-700 hover:text-gray-900 border-zinc-200 hover:bg-zinc-50'
          }`}
        >
          Previous Step
        </button>

        <button
          onClick={() => setActiveStep((prev) => Math.min(steps.length, prev + 1))}
          disabled={activeStep === steps.length}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition cursor-pointer border ${
            activeStep === steps.length
              ? 'opacity-40 cursor-not-allowed border-transparent'
              : isDark
                ? 'text-aquilia-400 border-aquilia-500/20 hover:border-aquilia-500/40 hover:bg-aquilia-500/10'
                : 'text-aquilia-600 border-aquilia-200 hover:border-aquilia-400 hover:bg-aquilia-50'
          }`}
        >
          Next Step
        </button>
      </div>

      {/* Next Steps Footer link */}
      <section className="mt-14">
        <NextSteps />
      </section>
    </div>
  )
}
