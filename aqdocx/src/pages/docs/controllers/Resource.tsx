import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Layout, Layers, CheckCircle, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ControllersResource() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Layout className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Resource & ViewSet Controllers
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.resource — Declarative CRUD controller abstractions</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          <code className="text-aquilia-500 font-mono">Resource[T]</code> provides a first-class declarative CRUD controller abstraction inspired by ViewSets. By defining standard methods (<code className="text-aquilia-500">list</code>, <code className="text-aquilia-500">retrieve</code>, <code className="text-aquilia-500">create</code>, <code className="text-aquilia-500">update</code>, <code className="text-aquilia-500">partial_update</code>, <code className="text-aquilia-500">destroy</code>), routes are automatically compiled with correct HTTP verbs and path parameter types.
        </p>
      </div>

      {/* Old vs New API Comparison */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Old API vs New API</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-red-400">Old Boilerplate (Plain Controller)</h3>
            <CodeBlock
              language="python"
              filename="old_controller.py"
              code={`class UserController(Controller):
    prefix = "/users"

    @GET("/")
    async def list_users(self, ctx):
        return await self.repo.list()

    @GET("/{id:int}")
    async def get_user(self, ctx, id: int):
        return await self.repo.get(id)

    @POST("/")
    async def create_user(self, ctx, body: UserContract):
        return await self.repo.create(body)

    @PUT("/{id:int}")
    async def update_user(self, ctx, id: int, body: UserContract):
        return await self.repo.update(id, body)`}
            />
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-emerald-400">New API (Resource Subclass)</h3>
            <CodeBlock
              language="python"
              filename="new_resource.py"
              code={`from aquilia.controller.resource import CRUDResource, action

class UserResource(CRUDResource[User]):
    prefix = "/users"
    id_param = "id"
    id_type = "int"

    async def list(self, ctx):
        return await self.repo.list()

    async def retrieve(self, ctx, id: int):
        return await self.repo.get(id)

    async def create(self, ctx, body: UserContract):
        return await self.repo.create(body)

    async def update(self, ctx, id: int, body: UserContract):
        return await self.repo.update(id, body)`}
            />
          </div>
        </div>
      </section>

      {/* CRUD Action Mapping Table */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Automatic Action Mapping
        </h2>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Method Name</th>
                <th className="text-left px-4 py-3 font-semibold">HTTP Verb</th>
                <th className="text-left px-4 py-3 font-semibold">Route Path</th>
                <th className="text-left px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['list', 'GET', '/', 'List all resources'],
                ['retrieve', 'GET', '/{id:type}', 'Fetch single resource by ID'],
                ['create', 'POST', '/', 'Create a new resource'],
                ['update', 'PUT', '/{id:type}', 'Replace existing resource'],
                ['partial_update', 'PATCH', '/{id:type}', 'Partially update resource'],
                ['destroy', 'DELETE', '/{id:type}', 'Delete resource'],
              ].map(([method, verb, path, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{method}</td>
                  <td className="px-4 py-2 font-mono text-xs text-emerald-400 font-bold">{verb}</td>
                  <td className="px-4 py-2 font-mono text-xs text-amber-400">{path}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* @action Decorator */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Custom Actions with @action
        </h2>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Use the <code className="text-aquilia-500 font-mono">@action</code> decorator to add custom endpoints beyond standard CRUD operations:
        </p>

        <CodeBlock
          language="python"
          filename="custom_actions.py"
          code={`from aquilia.controller.resource import Resource, action

class UserResource(Resource[User]):
    prefix = "/users"

    # Detail action: POST /users/{id:int}/deactivate
    @action(methods=["POST"], detail=True)
    async def deactivate(self, ctx, id: int):
        return {"status": "deactivated", "user_id": id}

    # Collection action: GET /users/active-count
    @action(methods=["GET"], detail=False, url_path="active-count")
    async def active_count(self, ctx):
        return {"count": 42}`}
        />
      </section>

      {/* Pre-composed Mixins */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <ArrowRight className="w-5 h-5 text-aquilia-400" />
          Resource Helpers & Mixins
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className={`p-4 rounded-xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
            <h3 className="font-mono text-aquilia-400 font-bold text-base mb-1">ReadOnlyResource[T]</h3>
            <p className="text-xs text-gray-400">Includes only <code className="text-white">ListMixin</code> and <code className="text-white">RetrieveMixin</code> (read-only endpoints).</p>
          </div>

          <div className={`p-4 rounded-xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
            <h3 className="font-mono text-aquilia-400 font-bold text-base mb-1">CRUDResource[T]</h3>
            <p className="text-xs text-gray-400">Includes all 5 mixins: List, Retrieve, Create, Update, and Destroy endpoints.</p>
          </div>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
