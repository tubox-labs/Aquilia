import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Shield, ArrowLeft } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersValidation() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Shield className="w-4 h-4" />
          Controllers
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Body Validation
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides declarative request body validation using the <DocTerm id="controller.validate_body">@validate_body</DocTerm> decorator. It integrates directly with Contracts to parse and enforce contracts on incoming payloads.
        </p>
      </div>

      {/* validate_body decorator */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>The @validate_body Decorator</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">@validate_body</code> decorator validates incoming request payloads before they reach the route handler. On success, it injects the validated dictionary as a <code className="text-aquilia-500">body</code> keyword argument. On validation failure, it returns a <code className="text-aquilia-500">422 Unprocessable Entity</code> response containing the validation errors.
        </p>

        <CodeBlock
          language="python"
          filename="validation_example.py"
          code={`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.controller.validation import validate_body
from myapp.users.contracts import CreateUserContract

class UsersController(Controller):
    prefix = "/users"

    @POST("/")
    @validate_body(CreateUserContract)
    async def create_user(self, ctx: RequestCtx, body: dict) -> Response:
        # body is fully validated and typed according to the Contract contract
        user = await self.user_service.create(**body)
        return Response.json({"id": user.id}, status=201)`}
        />
      </section>

      {/* Validation Faults */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Validation Faults</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Body validation issues trigger structured faults:
        </p>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Fault Class</th>
                <th className="text-left px-4 py-3 font-semibold">Fault Code</th>
                <th className="text-left px-4 py-3 font-semibold">HTTP Status</th>
                <th className="text-left px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['RequestBodyValidationFault', 'validation.body_invalid', '422', 'The request body fails the Contract seal constraints.'],
                ['RequestBodyParseFault', 'validation.body_parse_error', '400', 'The request body content could not be parsed (e.g. malformed JSON).'],
              ].map(([cls, code, status, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{cls}</td>
                  <td className="px-4 py-2 font-mono text-xs">{code}</td>
                  <td className="px-4 py-2 font-mono text-xs">{status}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Controllers Overview</span>
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
