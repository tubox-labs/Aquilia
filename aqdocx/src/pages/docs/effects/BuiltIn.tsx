import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, Workflow } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsBuiltIn() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / BUILT-IN EFFECTS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Effects
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          In addition to database transactions and caching, Aquilia provides four built-in effects covering message queues, asynchronous task workers, outbound HTTP connections, and unified object storage.
        </p>
      </div>

      {/* QueueEffect */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}>QueueEffect</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Acquires a message queue publisher scoped to a specific topic or channel. The <code className="text-aquilia-500">QueueProvider</code> connects to standard brokers like RabbitMQ or Redis Streams, falling back to an in-memory collector during testing:
        </p>

        <CodeBlock language="python" filename="queue_setup.py" highlightLines={[6, 9]}>{`from aquilia.effects import QueueEffect, QueueProvider

# 1. Register the provider
registry.register("Queue", QueueProvider(broker_url="redis://localhost:6379/0"))

# 2. Require the effect on a controller/handler
class LogController(Controller):
    effects = [QueueEffect("system_logs")]

    @Post("/")
    async def log_event(self, ctx):
        body = await ctx.json()
        await ctx.effects.queue.publish(body)`}</CodeBlock>
      </section>

      {/* TaskQueueEffect */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}>TaskQueueEffect</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Bridges the effect system with Aquilia's native background task runner. The <code className="text-aquilia-500">TaskQueueProvider</code> wraps the active <DocTerm id="tasks.TaskManager">TaskManager</DocTerm> to enqueue background jobs from request handlers:
        </p>

        <CodeBlock language="python" filename="task_setup.py" highlightLines={[6, 9]}>{`from aquilia.effects import TaskQueueProvider, QueueEffect

registry.register("Queue", TaskQueueProvider(task_manager=task_manager))

class TaskController(Controller):
    # Triggers task queue handle acquisition
    effects = [QueueEffect("default")]

    @Post("/run")
    async def run_job(self, ctx):
        # Enqueues task directly via TaskManager backend
        await ctx.effects.queue.enqueue("modules.users.tasks:send_welcome_email", user_id=42)`}</CodeBlock>
      </section>

      {/* HTTPEffect */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}>HTTPEffect</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Acquires a pre-configured outbound HTTP client instance. The <code className="text-aquilia-500">HTTPProvider</code> instantiates Aquilia's native <code className="text-aquilia-400">AsyncHTTPClient</code> with request pooling, timeouts, and custom headers:
        </p>

        <CodeBlock language="python" filename="http_setup.py" highlightLines={[5, 11]}>{`from aquilia.effects import HTTPEffect, HTTPProvider

# Register with target API URL
registry.register("HTTP", HTTPProvider(base_url="https://api.github.com", timeout=10.0))

class GithubController(Controller):
    effects = [HTTPEffect()]

    @Get("/repos")
    async def list_repos(self, ctx):
        response = await ctx.effects.http.get("/users/kuroyami/repos")
        return ctx.json(await response.json())`}</CodeBlock>
      </section>

      {/* StorageEffect */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}>StorageEffect</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Provides unified access to local or cloud storage buckets. The <code className="text-aquilia-500">StorageProvider</code> wraps registered storage backends, returning standard storage handles:
        </p>

        <CodeBlock language="python" filename="storage_setup.py" highlightLines={[5, 11]}>{`from aquilia.effects import StorageEffect, StorageProvider

# Register filesystem storage provider
registry.register("Storage", StorageProvider(root_path="./uploads"))

class UploadController(Controller):
    effects = [StorageEffect("avatars")]

    @Post("/")
    async def upload_avatar(self, ctx):
        file = await ctx.request.file("avatar")
        # Save file to avatars folder
        path = await ctx.effects.storage.save(file.filename, file.content)
        return ctx.json({"path": path})`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/effects/cache" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Cache Effect
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
