import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ContractsFacets() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <Link to="/docs/contracts/overview" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Contracts</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Facets</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Facets</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Atomic field-level primitives of a Contract contract. Each <DocTerm id="bp.facet">Facet</DocTerm> manages type coercion (cast), validation (seal), and output representation (mold).
        </p>
      </div>

      {/* Base Facet Options */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Base Facet Options</h2>
        <CodeBlock language="python">{`from aquilia.contracts import Facet

field = Facet(
    source="model_field",     # read from distinct model attribute
    required=True,            # fail CastFault if missing on inbound
    read_only=False,          # exclude from inbound cast
    write_only=False,         # exclude from outbound serialization
    default=None,             # fallback value
    allow_null=False,         # accept None
    allow_blank=False,        # accept empty string (TextFacet only)
    validators=[],            # additional validator callables
)`}</CodeBlock>
      </section>

      {/* Common Facets */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white','text-gray-900')}`}>Built-in Facets</h2>

        {/* Text */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>
            <DocTerm id="bp.text_facet">TextFacet</DocTerm>
          </h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Handles string properties with length boundaries and pattern matching.
          </p>
          <CodeBlock language="python">{`sku = TextFacet(max_length=50, pattern=r"^[A-Z0-9-]+$")`}</CodeBlock>
        </div>

        {/* Numeric */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>
            <DocTerm id="bp.int_facet">IntFacet</DocTerm>
          </h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Coerces numeric strings/floats to integers. Validates min_value and max_value. Rejects booleans.
          </p>
          <CodeBlock language="python">{`quantity = IntFacet(min_value=1, max_value=99)`}</CodeBlock>
        </div>

        {/* Special */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>
            <DocTerm id="bp.computed_facet">Computed</DocTerm>
          </h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Derived read-only fields computed via a function or method. Can also use the <DocTerm id="bp.computed_decorator">@computed</DocTerm> decorator.
          </p>
          <CodeBlock language="python">{`# Inline lambda computed facet
full_name = Computed(lambda bp: f"{bp.instance.first_name} {bp.instance.last_name}")

# Method decorator pattern
@computed
def display_title(self) -> str:
    return self.instance.title.upper()`}</CodeBlock>
        </div>
      </section>

      {/* Choice Facet */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Choice Constraint</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Restricts values to a specific set. Supports lists, dicts, or tuples:
        </p>
        <CodeBlock language="python">{`from aquilia.contracts import ChoiceFacet

# List choices
status = ChoiceFacet(choices=["draft", "published"])

# Dict choices (value -> description)
priority = ChoiceFacet(choices={"L": "Low", "H": "High"})`}</CodeBlock>
      </section>

      {/* Complete Reference */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white','text-gray-900')}`}>Facet Registry Reference</h2>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Facet</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Python Target</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['TextFacet', 'str', 'String fields with length & regex.'],
                ['IntFacet', 'int', 'Integer values. Rejects fractional input rather than truncating.'],
                ['FloatFacet', 'float', 'Floating point values.'],
                ['DecimalFacet', 'Decimal', 'Precision decimal values serialized as string.'],
                ['BoolFacet', 'bool', 'Truthiness/falsiness checks.'],
                ['DateTimeFacet', 'datetime', 'ISO 8601 timestamps.'],
                ['BytesFacet', 'bytes', 'Binary data over JSON as base64 or hex.'],
                ['PathFacet', 'PurePosixPath', 'Filesystem paths; rejects traversal and absolute paths.'],
                ['SecretFacet', 'Secret', 'Sensitive strings masked in repr/str and logs.'],
                ['MACAddressFacet', 'str', 'MAC addresses normalized to lowercase colon form.'],
                ['IPFacet', 'str', 'IPv4 and IPv6 addresses.'],
                ['Computed', 'Any', 'Eagerly evaluated derived fields.'],
                ['ChoiceFacet', 'Any', 'Enumerated values.'],
              ].map(([m, r, d]) => (
                <tr key={m}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400">
                    <DocTerm id={m === 'TextFacet' ? 'bp.text_facet' : m === 'IntFacet' ? 'bp.int_facet' : m === 'Computed' ? 'bp.computed_facet' : 'bp.facet'}>
                      {m}
                    </DocTerm>
                  </td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{r}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Typed primitives */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Typed Primitives</h2>
        <p className={`mb-6 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Added in v1.3.5. Four types that previously fell through to a permissive <code>TextFacet</code> or had no facet at all.
        </p>

        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>BytesFacet</h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Binary data over a JSON transport. Size constraints apply to the <em>decoded</em> length, which is what matters for memory.
          </p>
          <CodeBlock language="python">{`class UploadContract(Contract):
    payload = BytesFacet()                    # base64 (default)
    checksum = BytesFacet(encoding="hex")
    thumbnail = BytesFacet(max_length=64 * 1024)

UploadContract(data={"payload": "aGVsbG8="})
# validated_data: {"payload": b"hello"}`}</CodeBlock>
          <p className={`mt-3 text-sm ${t('text-gray-300','text-gray-600')}`}>
            Always bound <code>max_length</code> on a client-facing binary field. Base64 expands roughly 33%, so a modest request body still
            decodes to a large allocation.
          </p>
        </div>

        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>PathFacet</h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Filesystem paths validated as <code>pathlib.PurePosixPath</code>, so a payload validates identically regardless of server platform.
          </p>
          <CodeBlock language="python">{`class UploadContract(Contract):
    destination = PathFacet()

UploadContract(data={"destination": "reports/q3.pdf"})
# validated_data: {"destination": PurePosixPath('reports/q3.pdf')}

# Rejected by default:
#   "/etc/passwd"          -> Path must be relative
#   "../../etc/passwd"     -> Path may not contain '..' segments
#   "a\\x00b"               -> Path may not contain null bytes`}</CodeBlock>
          <p className={`mt-3 text-sm ${t('text-gray-300','text-gray-600')}`}>
            The defaults reject the two ways a client-supplied path escapes its root. Null bytes are refused unconditionally — they truncate at
            the OS layer, so a name passing an extension check can still open a different file. Relax with
            <code> must_be_relative=False</code> / <code>allow_traversal=True</code> only for paths that never originate from a request.
          </p>
        </div>

        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>SecretFacet</h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Sensitive strings that never appear in output or tracebacks. <code>write_only</code> by default.
          </p>
          <CodeBlock language="python">{`class LoginContract(Contract):
    password = SecretFacet(min_length=8)

secret = contract.validated_data["password"]
repr(secret)       # "Secret('**********')"
str(secret)        # "**********"
secret.reveal()    # "hunter2hunter2"

if secret == stored_secret:   # constant-time comparison
    ...`}</CodeBlock>
          <p className={`mt-3 text-sm ${t('text-gray-300','text-gray-600')}`}>
            Equality uses <code>hmac.compare_digest</code>, so comparing a submitted value against a stored one does not leak the shared-prefix
            length through timing. Masking defends against <em>accidental</em> disclosure — log lines, exception reports, debug pages — and is not
            a substitute for hashing or encryption at rest. Call <code>.reveal()</code> only at the point of use.
          </p>
        </div>

        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>MACAddressFacet</h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Accepts colon, dash, and Cisco notations, normalizing at validation so downstream comparisons and database lookups do not each
            reimplement it.
          </p>
          <CodeBlock language="python">{`class DeviceContract(Contract):
    mac = MACAddressFacet()

# "AA:BB:CC:DD:EE:FF" -> "aa:bb:cc:dd:ee:ff"
# "aa-bb-cc-dd-ee-ff" -> "aa:bb:cc:dd:ee:ff"
# "aabb.ccdd.eeff"    -> "aa:bb:cc:dd:ee:ff"`}</CodeBlock>
        </div>

        <div>
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>Annotation Routing</h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            These types resolve to the right facet from a plain annotation:
          </p>
          <CodeBlock language="python">{`import ipaddress, pathlib
from aquilia.contracts.facets import Secret

class DeviceContract(Contract):
    address: ipaddress.IPv4Address    # IPFacet
    config_path: pathlib.Path         # PathFacet
    api_key: Secret                   # SecretFacet
    payload: bytes                    # BytesFacet`}</CodeBlock>
        </div>
      </section>

      {/* IntFacet behavior change */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Integer Coercion</h2>
        <CodeBlock language="python">{`class QuantityContract(Contract):
    qty = IntFacet()

QuantityContract(data={"qty": 3.0}).is_sealed()   # True — integral float
QuantityContract(data={"qty": 3.9}).errors
# {"qty": ["Expected integer, got non-integer number 3.9"]}`}</CodeBlock>
        <div className={`mt-4 p-4 rounded-lg border ${t('bg-amber-500/5 border-amber-500/20','bg-amber-50 border-amber-200')}`}>
          <p className={`text-sm ${t('text-gray-300','text-gray-700')}`}>
            <strong className={t('text-amber-400','text-amber-700')}>Changed in v1.3.5.</strong> <code>3.9</code> was previously truncated to
            <code> 3</code> while the string <code>&quot;3.9&quot;</code> was correctly rejected — the same logical input behaved differently
            depending on wire type. Silent truncation of a quantity or a price in cents is a data-integrity bug that surfaces far from its cause.
            <code> NaN</code> and <code>Infinity</code> are now rejected explicitly.
          </p>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/contracts" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/contracts/projections" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Projections <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
