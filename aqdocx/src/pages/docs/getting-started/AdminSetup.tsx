import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import {
  Settings, Terminal, Database, Activity,
  Layers, Layout, ShieldCheck, Wrench, AlertTriangle,
  Lock
} from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AdminSetupPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 relative admin-setup-page">
      {/* Background Radial Glow */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.06)_0,transparent_70%)] pointer-events-none print:hidden" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.04)_0,transparent_75%)] pointer-events-none print:hidden" />

      {/* Hero Header */}
      <div className="relative mb-16">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-aquilia-500/20 to-emerald-500/5 flex items-center justify-center">
            <Settings className="w-6 h-6 text-aquilia-400 animate-pulse" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-extrabold tracking-tighter gradient-text font-mono relative group inline-block">
                Admin Panel Setup
                <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-gradient-to-r from-aquilia-500 to-transparent" />
              </span>
            </h1>
            <p className={`text-xs tracking-wider uppercase font-mono mt-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              aquilia.admin &bull; Enterprise Operational Control Center
            </p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia comes with a built-in admin dashboard (<strong>AquilAdmin</strong>) that provides real-time control,
          live monitoring, and configuration analysis. This system is compiled ahead-of-time, uses sandboxed Jinja
          templates, and secures operations with Argon2id hashing and built-in rate-limiting guards.
        </p>
      </div>

      {/* Open Dashboard Features List */}
      <section className="mb-20">
        <div className="flex items-center gap-2 mb-8">
          <Layout className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Operational Modules
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l border-aquilia-500/30 dark:border-aquilia-500/10">
            <div className="flex items-center gap-2 text-blue-400 font-semibold text-sm">
              <Database className="w-4 h-4" />
              <span>ORM & Migrations</span>
            </div>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Browse and edit model data, run, verify, or rollback database migrations in real time, and inspect queries using the typed SQL planner.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l border-aquilia-500/30 dark:border-aquilia-500/10">
            <div className="flex items-center gap-2 text-purple-400 font-semibold text-sm">
              <Activity className="w-4 h-4" />
              <span>System & Docker</span>
            </div>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Monitor CPU, memory, disk usage, python runtime statistics, and interact directly with Docker containers and Kubernetes Pods.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l border-aquilia-500/30 dark:border-aquilia-500/10">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
              <ShieldCheck className="w-4 h-4" />
              <span>Security & Audit</span>
            </div>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Manage superuser and staff roles, inspect secure audit trails, provision custom API keys, and enforce progressive account lockout rules.
            </p>
          </div>
        </div>
      </section>

      {/* Automated Setup Timeline */}
      <section className="mb-20">
        <div className="flex items-center gap-2 mb-8">
          <Terminal className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Automated Setup
          </h2>
        </div>

        <p className={`mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The quickest way to configure the admin dashboard is by executing the automated CLI setup command.
          It scans your environment, configures sessions, database pools, and template registries automatically.
        </p>

        <div className="mb-10">
          <CodeBlock code={`aq admin setup`} language="bash" />
        </div>

        {/* Process Flow Steps */}
        <div className="space-y-10 relative border-l-2 border-gray-100 dark:border-zinc-800 ml-4 pl-8">
          {/* Step 1 */}
          <div className="relative">
            <div className="absolute -left-[39px] top-0.5 w-4 h-4 rounded-full bg-aquilia-500 ring-4 ring-aquilia-500/20 dark:ring-aquilia-500/10 flex items-center justify-center text-[10px] text-white font-bold" />
            <h4 className={`text-sm font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Imports & Integrations Check</h4>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              The CLI injects the necessary classes (<DocTerm id="config.admin_integration">AdminIntegration</DocTerm>, <code>SessionPolicy</code>, etc.) and sets up security modules in <code>workspace.py</code>.
            </p>
          </div>

          {/* Step 2 */}
          <div className="relative">
            <div className="absolute -left-[39px] top-0.5 w-4 h-4 rounded-full bg-aquilia-500 ring-4 ring-aquilia-500/20 dark:ring-aquilia-500/10 flex items-center justify-center text-[10px] text-white font-bold" />
            <h4 className={`text-sm font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Sessions Configuration</h4>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Enables secure cookie transport protocols, custom timeouts, and absolute token rotations for admin session persistence.
            </p>
          </div>

          {/* Step 3 */}
          <div className="relative">
            <div className="absolute -left-[39px] top-0.5 w-4 h-4 rounded-full bg-aquilia-500 ring-4 ring-aquilia-500/20 dark:ring-aquilia-500/10 flex items-center justify-center text-[10px] text-white font-bold" />
            <h4 className={`text-sm font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Schema Initialization</h4>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Generates the required database tables automatically for users, groups, permissions, audit trails, and active sessions.
            </p>
          </div>

          {/* Step 4 */}
          <div className="relative">
            <div className="absolute -left-[39px] top-0.5 w-4 h-4 rounded-full bg-aquilia-500 ring-4 ring-aquilia-500/20 dark:ring-aquilia-500/10 flex items-center justify-center text-[10px] text-white font-bold" />
            <h4 className={`text-sm font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Superuser Creation</h4>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Prompts you interactively to create your initial superuser credentials. Staff accounts can be added later.
            </p>
          </div>
        </div>
      </section>

      {/* CLI Reference Section */}
      <section className="mb-20">
        <div className="flex items-center gap-2 mb-8">
          <Wrench className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            CLI Command Reference
          </h2>
        </div>

        <p className={`mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>aq admin</code> CLI toolchain provides diagnostics, security administration, user account management, and operational commands.
        </p>

        <div className="space-y-12">
          {/* Command 1 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_setup">aq admin setup</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Automatically configures <code>workspace.py</code> with default dependencies, runs database table checks/migrations, and configures the initial superuser.
            </p>
            <CodeBlock code={`aq admin setup --database-url="postgresql://user:pass@localhost:5432/db" --non-interactive`} language="bash" />
            <div className="flex flex-col gap-2.5 mt-3 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Flags & Options</span>
              <div className={`grid grid-cols-[140px_1fr] gap-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">-y, --non-interactive</code>
                <span>Bypasses confirmation queries and proceeds with default updates.</span>
                <code className="font-mono text-aquilia-400">--database-url TEXT</code>
                <span>Connection URL override written directly to the database integration builder.</span>
              </div>
            </div>
          </div>

          {/* Command 2 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_check">aq admin check</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Runs pre-flight validation on admin dashboard dependencies. Confirms integrations, cookie policies, database migrations, asset directories, and container configurations.
            </p>
            <CodeBlock code={`aq admin check --fix --json`} language="bash" />
            <div className="flex flex-col gap-2.5 mt-3 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Flags & Options</span>
              <div className={`grid grid-cols-[140px_1fr] gap-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">--fix</code>
                <span>Attempts to dynamically uncomment disabled session lines inside <code>workspace.py</code>.</span>
                <code className="font-mono text-aquilia-400">--json</code>
                <span>Outputs test results as structured JSON metadata, suitable for CI pipelines.</span>
              </div>
            </div>
          </div>

          {/* Command 3 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_createsuperuser">aq admin createsuperuser</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Creates a superuser (role: <code>superadmin</code>) inside the database. Superusers possess full administrative rights over modules, custom permissions, settings, and user groups.
            </p>
            <CodeBlock code={`aq admin createsuperuser --username=admin --email=ops@aquilia.dev --password="SuperSecurePassword123!"`} language="bash" />
            <div className="flex flex-col gap-2.5 mt-3 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Flags & Options</span>
              <div className={`grid grid-cols-[140px_1fr] gap-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">--username TEXT</code>
                <span>Operator login username (minimum 2 characters, unique).</span>
                <code className="font-mono text-aquilia-400">--email TEXT</code>
                <span>Operations email address (unique, validated format).</span>
                <code className="font-mono text-aquilia-400">--password TEXT</code>
                <span>Secure credential string. Prompted interactively if omitted. Enforces standard complexity.</span>
                <code className="font-mono text-aquilia-400">--first-name TEXT</code>
                <span>Optional first name metadata.</span>
                <code className="font-mono text-aquilia-400">--last-name TEXT</code>
                <span>Optional last name metadata.</span>
              </div>
            </div>
          </div>

          {/* Command 4 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_createstaff">aq admin createstaff</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Creates a staff user (role: <code>staff</code>). Staff operators have access to the dashboard but cannot manage system permissions, view audit logs, or edit other administrator users.
            </p>
            <CodeBlock code={`aq admin createstaff --username=moderator --email=mod@aquilia.dev --first-name=Jane`} language="bash" />
            <div className="flex flex-col gap-2.5 mt-3 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Flags & Options</span>
              <div className={`grid grid-cols-[140px_1fr] gap-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">--username TEXT</code>
                <span>Staff operator login username.</span>
                <code className="font-mono text-aquilia-400">--email TEXT</code>
                <span>Staff operations email address.</span>
                <code className="font-mono text-aquilia-400">--password TEXT</code>
                <span>Secure password. Prompted interactively if omitted.</span>
                <code className="font-mono text-aquilia-400">--first-name TEXT</code>
                <span>Optional first name metadata.</span>
                <code className="font-mono text-aquilia-400">--last-name TEXT</code>
                <span>Optional last name metadata.</span>
              </div>
            </div>
          </div>

          {/* Command 5 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_listusers">aq admin listusers</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Queries the <code>aq_admin_users</code> table to list registered accounts. Shows ID, username, email, active status, user role, and join date.
            </p>
            <CodeBlock code={`aq admin listusers --active-only --json`} language="bash" />
            <div className="flex flex-col gap-2.5 mt-3 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Flags & Options</span>
              <div className={`grid grid-cols-[140px_1fr] gap-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">--active-only</code>
                <span>Filters out accounts that have been deactivated.</span>
                <code className="font-mono text-aquilia-400">--json</code>
                <span>Serializes user objects into a raw JSON list.</span>
                <code className="font-mono text-aquilia-400">--database-url TEXT</code>
                <span>Connection string override.</span>
              </div>
            </div>
          </div>

          {/* Command 6 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_changepassword">aq admin changepassword</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Securely updates the login password for the specified user after checking standard complexity policies.
            </p>
            <CodeBlock code={`aq admin changepassword moderator --password="NewUltraStrongPassword789!"`} language="bash" />
            <div className="flex flex-col gap-2.5 mt-3 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Flags & Options</span>
              <div className={`grid grid-cols-[140px_1fr] gap-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">USERNAME</code>
                <span>Target account username.</span>
                <code className="font-mono text-aquilia-400">--password TEXT</code>
                <span>New password. Prompted and masked if omitted.</span>
                <code className="font-mono text-aquilia-400">--database-url TEXT</code>
                <span>Connection string override.</span>
              </div>
            </div>
          </div>

          {/* Command 7 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_status">aq admin status</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Outputs the dashboard registration state. Inspects models registered via <code>autodiscover()</code>, showing their class representations and list fields.
            </p>
            <CodeBlock code={`aq admin status`} language="bash" />
          </div>

          {/* Command 8 */}
          <div className="flex flex-col gap-2 relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="cli.admin_audit">aq admin audit</DocTerm>
            </h3>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
              Queries administrative audit records. Returns chronological logs showing execution timestamps, activity types (logins, data modifications), target models, and operator usernames.
            </p>
            <CodeBlock code={`aq admin audit --limit=100 --action=create --user=admin`} language="bash" />
            <div className="flex flex-col gap-2.5 mt-3 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Flags & Options</span>
              <div className={`grid grid-cols-[140px_1fr] gap-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">--limit INTEGER</code>
                <span>Maximum entries to return (default is 50).</span>
                <code className="font-mono text-aquilia-400">--action TEXT</code>
                <span>Action filter (e.g. <code>login</code>, <code>create</code>, <code>update</code>, <code>delete</code>, <code>settings_change</code>).</span>
                <code className="font-mono text-aquilia-400">--user TEXT</code>
                <span>Username filter.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Password Complexity Requirements Detail */}
      <section className="mb-20">
        <div className="flex items-center gap-2 mb-6">
          <Lock className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Password Policy Enforcement
          </h2>
        </div>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          All user passwords created via CLI or the admin controller are validated against strict strength checks.
          A password will be rejected unless it satisfies all of the following rules:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pl-6 border-l border-aquilia-500/20">
          <div className="flex flex-col gap-1">
            <span className="font-bold text-aquilia-400 text-sm">Casing & Length</span>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Must be at least <strong>8 characters</strong> and contain both <strong>uppercase</strong> and <strong>lowercase</strong> characters.
            </p>
          </div>
          <div className="flex flex-col gap-1">
            <span className="font-bold text-aquilia-400 text-sm">Digits & Special Symbols</span>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Must contain at least <strong>one numerical digit</strong> and at least <strong>one special symbol</strong> (e.g., <code>!@#$%^&*()</code>).
            </p>
          </div>
        </div>
      </section>

      {/* Workspace Manual Integration */}
      <section className="mb-20">
        <div className="flex items-center gap-2 mb-6">
          <Layers className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Workspace Configuration
          </h2>
        </div>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          To configure the admin integration manually, register the <DocTerm id="config.admin_integration">AdminIntegration</DocTerm> class 
          in your root <code>workspace.py</code>:
        </p>

        <CodeBlock code={`# workspace.py
from datetime import timedelta
from aquilia import Workspace
from aquilia.sessions import SessionPolicy, TransportPolicy
from aquilia.integrations import (
    DatabaseIntegration,
    AdminIntegration,
    AdminModules,
    AdminSecurity
)

workspace = (
    Workspace("my-app")
    
    # 1. Active database is required to store users/permissions
    .integrate(DatabaseIntegration(url="sqlite:///db.sqlite3"))
    
    # 2. Session policy is required for secure authentication cookie transport
    .sessions(
        policies=[
            SessionPolicy(
                name="default",
                ttl=timedelta(days=7),
                idle_timeout=timedelta(hours=1),
                transport=TransportPolicy(
                    cookie_name="aquilia_admin_session",
                    cookie_secure=False,  # Set True in production (HTTPS)
                    cookie_httponly=True,
                    cookie_samesite="lax",
                ),
            ),
        ],
    )
    
    # 3. Integrate the Admin dashboard module
    .integrate(
        AdminIntegration(
            url_prefix="/admin",
            site_title="Core Admin Panel",
            auto_discover=True,
            modules=AdminModules(
                monitoring=True,      # Opt-in system diagnostics
                containers=True,      # Opt-in Docker panel
                audit=True            # Opt-in security audit logs
            ),
            security=AdminSecurity(
                password_min_length=12,
                rate_limit_max_attempts=5
            )
        )
    )
)`} language="python" />
      </section>

      {/* Fluent Integrations API Reference */}
      <section className="mb-20">
        <div className="flex items-center gap-2 mb-8">
          <Layers className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Fluent Integrations API
          </h2>
        </div>

        <p className={`mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>aquilia.integrations.admin</code> package provides builder interfaces to dynamically configure system panels.
        </p>

        <div className="space-y-12">
          {/* AdminModules Builder */}
          <div className="relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="config.admin_modules">AdminModules</DocTerm>
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-3`}>
              Toggles administrative modules. Supports both standard dataclass overrides and method-based fluent configurations.
            </p>
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Fluent Methods</span>
              <div className={`grid grid-cols-[200px_1fr] gap-x-4 gap-y-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">.enable_all()</code>
                <span>Activates absolutely all modules.</span>
                <code className="font-mono text-aquilia-400">.disable_all()</code>
                <span>Deactivates all optional modules.</span>
                <code className="font-mono text-aquilia-400">.enable_orm() / .disable_orm()</code>
                <span>Toggles database entry browsers.</span>
                <code className="font-mono text-aquilia-400">.enable_migrations() / .disable_migrations()</code>
                <span>Toggles visual migration controllers.</span>
                <code className="font-mono text-aquilia-400">.enable_monitoring() / .disable_monitoring()</code>
                <span>Toggles resource monitor pages.</span>
                <code className="font-mono text-aquilia-400">.enable_containers() / .disable_containers()</code>
                <span>Toggles the Docker panel.</span>
                <code className="font-mono text-aquilia-400">.enable_pods() / .disable_pods()</code>
                <span>Toggles the Kubernetes monitoring dashboard.</span>
                <code className="font-mono text-aquilia-400">.enable_tasks() / .disable_tasks()</code>
                <span>Toggles background cron schedulers.</span>
                <code className="font-mono text-aquilia-400">.enable_audit() / .disable_audit()</code>
                <span>Toggles the administrative action timeline.</span>
                <code className="font-mono text-aquilia-400">.enable_api_keys() / .disable_api_keys()</code>
                <span>Toggles developer API key creation.</span>
                <code className="font-mono text-aquilia-400">.with_(**overrides: bool)</code>
                <span>Returns a copy with overridden key states.</span>
              </div>
            </div>
          </div>

          {/* AdminSecurity Builder */}
          <div className="relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <DocTerm id="config.admin_security">AdminSecurity</DocTerm>
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-3`}>
              Manages brute-force protection, lockout increments, password security thresholds, and security headers.
            </p>
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Fluent Methods</span>
              <div className={`grid grid-cols-[200px_1fr] gap-x-4 gap-y-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">.strict_password_policy()</code>
                <span>Restricts passwords to a minimum length of 12 and requires special symbols, numbers, and case mixes.</span>
                <code className="font-mono text-aquilia-400">.relaxed_password_policy()</code>
                <span>Lowers password minimum length requirement to 8 characters and disables symbols complexity tests.</span>
                <code className="font-mono text-aquilia-400">.csrf_enabled_set(enabled: bool)</code>
                <span>Configures session validation tokens.</span>
                <code className="font-mono text-aquilia-400">.no_csrf()</code>
                <span>Disables active Cross-Site Request Forgery tokens.</span>
                <code className="font-mono text-aquilia-400">.no_rate_limit()</code>
                <span>Disables brute force lockout parameters.</span>
                <code className="font-mono text-aquilia-400">.no_security_headers()</code>
                <span>Disables frame embedding block headers.</span>
              </div>
            </div>
          </div>

          {/* AdminAudit Builder */}
          <div className="relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              AdminAudit
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-3`}>
              Controls audit log preservation limits and details what categories of actions are archived.
            </p>
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Fluent Methods</span>
              <div className={`grid grid-cols-[200px_1fr] gap-x-4 gap-y-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">.enable() / .disable()</code>
                <span>Toggles audit logs collection.</span>
                <code className="font-mono text-aquilia-400">.set_max_entries(n: int)</code>
                <span>Limits the audit log database count (FIFO eviction kicks in when exceeded, minimum value is 100).</span>
                <code className="font-mono text-aquilia-400">.log_logins_set(enabled: bool)</code>
                <span>Toggles archiving user login attempts.</span>
                <code className="font-mono text-aquilia-400">.log_views_set(enabled: bool)</code>
                <span>Toggles logging admin browser panel loads.</span>
                <code className="font-mono text-aquilia-400">.log_searches_set(enabled: bool)</code>
                <span>Toggles archiving query search details.</span>
                <code className="font-mono text-aquilia-400">.exclude_actions(*actions: str)</code>
                <span>Excludes specific actions (e.g. <code>view</code>, <code>search</code>) from being archived.</span>
              </div>
            </div>
          </div>

          {/* AdminMonitoring Builder */}
          <div className="relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              AdminMonitoring
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-3`}>
              Configures system performance metrics collection parameters.
            </p>
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Fluent Methods</span>
              <div className={`grid grid-cols-[200px_1fr] gap-x-4 gap-y-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">.enable() / .disable()</code>
                <span>Toggles resource metric charts page.</span>
                <code className="font-mono text-aquilia-400">.all_metrics()</code>
                <span>Includes cpu, memory, disk, network, process, python, system, and health checks.</span>
                <code className="font-mono text-aquilia-400">.metrics_set(*names: str)</code>
                <span>Selects a subset of system metrics to track.</span>
                <code className="font-mono text-aquilia-400">.refresh_interval_set(seconds: int)</code>
                <span>Sets the interval to query system utilization metrics (minimum value is 5 seconds).</span>
              </div>
            </div>
          </div>

          {/* AdminSidebar Builder */}
          <div className="relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              AdminSidebar
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-3`}>
              Allows show/hide configuration of menu groups inside the admin dashboard side navigation panel.
            </p>
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Fluent Methods</span>
              <div className={`grid grid-cols-[200px_1fr] gap-x-4 gap-y-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">.show_all() / .hide_all()</code>
                <span>Toggles visibility for all navigation categories.</span>
                <code className="font-mono text-aquilia-400">.show_overview() / .hide_overview()</code>
                <span>Toggles the main landing page menu.</span>
                <code className="font-mono text-aquilia-400">.show_data() / .hide_data()</code>
                <span>Toggles the ORM and database section.</span>
                <code className="font-mono text-aquilia-400">.show_system() / .hide_system()</code>
                <span>Toggles the performance charts section.</span>
                <code className="font-mono text-aquilia-400">.show_infrastructure() / .hide_infrastructure()</code>
                <span>Toggles Docker and Pods modules.</span>
                <code className="font-mono text-aquilia-400">.show_security() / .hide_security()</code>
                <span>Toggles accounts and permissions items.</span>
                <code className="font-mono text-aquilia-400">.show_devtools() / .hide_devtools()</code>
                <span>Toggles the settings and query analyzer categories.</span>
              </div>
            </div>
          </div>

          {/* AdminContainers Builder */}
          <div className="relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              AdminContainers
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-3`}>
              Controls Docker daemon communication parameters and restricts allowed container operations.
            </p>
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Fluent Methods</span>
              <div className={`grid grid-cols-[200px_1fr] gap-x-4 gap-y-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">.docker_socket(path: str)</code>
                <span>Sets connection path to local daemon (e.g. <code>/var/run/docker.sock</code>).</span>
                <code className="font-mono text-aquilia-400">.read_only()</code>
                <span>Restricts interaction. Disables starting, stopping, building, pruning, exec shells, or deleting containers.</span>
              </div>
            </div>
          </div>

          {/* AdminPods Builder */}
          <div className="relative pl-6 border-l-2 border-aquilia-500/30 dark:border-aquilia-500/10">
            <h3 className={`text-base font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              AdminPods
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mb-3`}>
              Governs Kubernetes operational modes, restricting pod deletions, context updates, and shell execution capabilities.
            </p>
            <div className="flex flex-col gap-1 text-xs">
              <span className="font-semibold uppercase tracking-wider text-aquilia-500 text-[10px]">Fluent Methods</span>
              <div className={`grid grid-cols-[200px_1fr] gap-x-4 gap-y-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <code className="font-mono text-aquilia-400">.all_namespaces()</code>
                <span>Instructs the client to fetch details across all active Kubernetes namespaces.</span>
                <code className="font-mono text-aquilia-400">.read_only()</code>
                <span>Disables container scaling, deployments, context switches, apply commands, and pod termination.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Troubleshooting Section */}
      <section className="mb-20">
        <div className="flex items-center gap-2 mb-8">
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Common Pitfalls
          </h2>
        </div>

        <div className="space-y-6">
          <div className="flex gap-4 relative pl-6 border-l-2 border-amber-500/20">
            <div className="text-amber-500 font-bold text-sm">!</div>
            <div>
              <h4 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Dashboard Assets Fail to Load</h4>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mt-1 leading-relaxed`}>
                Ensure that <code>StaticFilesIntegration</code> is registered in your <code>workspace.py</code>. 
                Without static files, the browser cannot download CSS and JS bundles.
              </p>
            </div>
          </div>

          <div className="flex gap-4 relative pl-6 border-l-2 border-amber-500/20">
            <div className="text-amber-500 font-bold text-sm">!</div>
            <div>
              <h4 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>CSRF Validation Errors on Login</h4>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mt-1 leading-relaxed`}>
                If running locally without HTTPS, make sure <code>cookie_secure=False</code> is set inside your 
                <code>TransportPolicy</code>. Otherwise, cookies will not be sent back to local endpoints.
              </p>
            </div>
          </div>

          <div className="flex gap-4 relative pl-6 border-l-2 border-amber-500/20">
            <div className="text-amber-500 font-bold text-sm">!</div>
            <div>
              <h4 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Docker or Pods Panels Grayed Out</h4>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mt-1 leading-relaxed`}>
                These panels are disabled if <code>docker</code> or <code>kubectl</code> CLI binaries are missing from 
                your system PATH. Ensure Docker is running and Kubeconfig context is set.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Next Steps */}
      <NextSteps
        items={[
          { text: 'Introduction to Core subsystems', link: '/docs' },
          { text: 'Database and ORM reference', link: '/docs/database/engine' },
          { text: 'Testing your Application', link: '/docs/testing' }
        ]}
      />
    </div>
  )
}
