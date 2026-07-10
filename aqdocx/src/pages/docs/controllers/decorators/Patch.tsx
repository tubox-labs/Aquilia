import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Zap, ArrowLeft, ArrowRight, Edit, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../../components/NextSteps'

export function DecoratorPatch() {
    const { theme } = useTheme()
    const isDark = theme === 'dark'

    return (
        <div className="max-w-4xl mx-auto space-y-12 pb-16">
            <div>
                <Link to="/docs/controllers/decorators" className={`flex items-center gap-2 text-sm mb-4 ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>
                    <ArrowLeft className="w-4 h-4" /> Back to Decorators
                </Link>
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-yellow-500/10 text-yellow-500">
                        <Zap className="w-6 h-6 animate-pulse" />
                    </div>
                    <h1 className={`text-4xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        @PATCH
                    </h1>
                </div>
                <p className={`text-xl ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                    The <code>@PATCH</code> decorator handles HTTP PATCH requests, used for <strong>partial modifications</strong> of a resource.
                    Clients only need to send the fields they wish to change.
                </p>
            </div>

            {/* Usage */}
            <section className="space-y-4">
                <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Basic Usage</h2>
                <CodeBlock
                    code={`from aquilia import Controller, PATCH, RequestCtx, Response, exceptions
 
class UsersController(Controller):
    prefix = "/users"
 
    @PATCH("/«id:int»")
    async def partial_update(self, ctx: RequestCtx, id: int):
        user = await self.repo.get_or_404(id)
        
        # Merge changes from request body
        payload = await ctx.json()
        updated_user = await self.repo.update(user, payload)
        
        return Response.json(updated_user)`}
                    language="python"
                />
            </section>

            {/* Deep Dive: Partial Validation */}
            <section className="space-y-4">
                <div className="flex items-center gap-2 mb-4">
                    <Edit className="w-5 h-5 text-aquilia-500" />
                    <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Partial Updates with Contracts</h2>
                </div>
                <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                    In Aquilia, partial updates are modeled using optional fields in a Contract or by utilizing projected references to validate a subset of fields.
                </p>

                <div className="p-4 border-l-4 border-yellow-500 bg-yellow-500/5 rounded-r-xl">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5" />
                        <div>
                            <h4 className={`font-semibold ${isDark ? 'text-yellow-250' : 'text-yellow-800'}`}>Schema Tip</h4>
                            <p className={`text-sm ${isDark ? 'text-yellow-300' : 'text-yellow-700'}`}>
                                For partial PATCH operations, define the fields in your update contract as optional (e.g. using <code>Field(required=False)</code> or having a default value).
                            </p>
                        </div>
                    </div>
                </div>

                <CodeBlock
                    code={`@PATCH(
    "/«id:int»",
    request_contract=UserUpdateContract,
    response_contract=UserContract
)
async def update(self, ctx: RequestCtx, id: int, body: dict):
    user = await self.repo.patch(id, body)
    return Response.json(user)`}
                    language="python"
                />
            </section>

            {/* Navigation */}
            <div className="flex justify-between mt-8">
                <Link to="/docs/controllers/decorators/put" className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
                    <ArrowLeft className="w-4 h-4" /> Previous: @PUT
                </Link>
                <Link to="/docs/controllers/decorators/delete" className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
                    Next: @DELETE <ArrowRight className="w-4 h-4" />
                </Link>
            </div>
        
            <NextSteps />
        </div>
    )
}