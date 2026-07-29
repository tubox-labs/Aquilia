import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ContractsValidationControl() {
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
        <span className={t('text-gray-300','text-gray-600')}>Validation Control</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Validation Control</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Ordering, conditions, and groups on <DocTerm id="bp.ward">@ward</DocTerm>; plus frozen Contracts, copy-with-update, and alternate data sources.
        </p>
        <p className={`mt-3 text-sm ${t('text-gray-400','text-gray-500')}`}>Added in v1.3.5. Everything here is additive — a Contract that declares none of it behaves exactly as before.</p>
      </div>

      {/* Ordering */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Ordering</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Lower <code>order</code> runs first. Wards sharing an order keep definition order — the sort is stable, so a Contract that sets no
          order behaves exactly as before. Use it when one ward&apos;s rejection makes another&apos;s work redundant:
        </p>
        <CodeBlock language="python">{`class OrderContract(Contract):
    @ward(order=-10)
    def total_not_negative(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(order=0)          # default
    async def payment_authorized(self, data):
        ...                  # expensive: hits the payment provider`}</CodeBlock>
      </section>

      {/* Conditions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Conditional Rules</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <code>when</code> receives the validated data. Moving the condition into metadata means the rule&apos;s applicability is inspectable
          rather than buried in an <code>if</code> at the top of the body:
        </p>
        <CodeBlock language="python">{`class OrderContract(Contract):
    @ward(when=lambda data: data["kind"] == "physical")
    def needs_shipping_address(self, data):
        if not data.get("shipping_address"):
            self.reject("shipping_address", "Required for physical orders")`}</CodeBlock>
        <div className={`mt-4 p-4 rounded-lg border ${t('bg-blue-500/5 border-blue-500/20','bg-blue-50 border-blue-200')}`}>
          <p className={`text-sm ${t('text-gray-300','text-gray-700')}`}>
            <strong className={t('text-blue-400','text-blue-700')}>Edge case.</strong> A predicate that raises is treated as &quot;does not
            apply&quot;. The predicate is a routing decision, not a validation rule — a broken predicate must not manufacture a field error
            attributed to the ward it was gating, since that error would name the wrong field and the wrong cause.
          </p>
        </div>
      </section>

      {/* Groups */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Validation Groups</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Different operations need different rule sets. Groups replace the pattern of a separate Contract subclass per operation:
        </p>
        <CodeBlock language="python">{`class UserContract(Contract):
    @ward(groups=("registration",))
    def password_strength(self, data): ...

    @ward(groups=("admin",))
    def role_assignable(self, data): ...

    @ward
    def email_wellformed(self, data):    # no groups — always runs
        ...`}</CodeBlock>
        <p className={`mt-4 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>Select groups per pass:</p>
        <CodeBlock language="python">{`contract.is_sealed(groups="registration")
contract.is_sealed(groups=["registration", "admin"])
await contract.is_sealed_async(groups="checkout")`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <strong>An ungrouped ward always runs.</strong> It expresses an invariant that holds regardless of which group the caller asked for —
          an email must be well-formed whether or not this is a registration. Grouping an invariant would silently disable it for every pass that
          did not name its group. Groups propagate to nested Contracts.
        </p>
      </section>

      {/* fail_fast */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Fail Fast</h2>
        <CodeBlock language="python">{`class OrderContract(Contract):
    class Spec:
        fail_fast = True

    @ward
    def first(self, data): ...
    @ward
    def second(self, data): ...    # never runs if \`first\` rejected`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Default is <code>False</code>, unchanged — accumulating every error is right for a form, where a user should see all problems at once.
          <code> fail_fast</code> suits pipelines where a later rule&apos;s output would be noise. It applies to the ward phase only; structural
          field validation always accumulates.
        </p>
      </section>

      {/* Frozen / equality / copy */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Frozen, Equality, and Copy</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <code>is_sealed()</code> returning <code>True</code> is a guarantee that the data satisfied every rule. That guarantee expires the
          moment a caller assigns to a field, so <code>Spec.frozen</code> makes it durable:
        </p>
        <CodeBlock language="python">{`class ConfigContract(Contract):
    port = IntFacet()

    class Spec:
        frozen = True

config = ConfigContract(data={"port": 8000})
config.is_sealed()
config.validated_data["port"] = 9000
# TypeError: DataObject is frozen and cannot be modified`}</CodeBlock>
        <p className={`mt-6 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Two Contracts are equal when they are the same class and carry the same validated data. Unvalidated Contracts compare on their raw
          input, so a comparison before sealing is still meaningful rather than degrading to identity:
        </p>
        <CodeBlock language="python">{`a = UserContract(data={"name": "Ada"})
b = UserContract(data={"name": "Ada"})
a.is_sealed(); b.is_sealed()
a == b     # True

hash(a)
# TypeError: UserContract is unhashable (its validated data is mutable)`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Contracts stay unhashable deliberately. Validated data is mutable by default, so a hash computed at insertion time would go stale and
          the object would become unfindable in its own dict. An explicit <code>__hash__</code> that raises names the reason, where defining
          <code> __eq__</code> alone would have set <code>__hash__ = None</code> silently.
        </p>
        <p className={`mt-6 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <code>copy(update=...)</code> derives a new Contract with fields replaced, re-validating by default — an override can violate a
          constraint the original satisfied:
        </p>
        <CodeBlock language="python">{`updated = contract.copy(update={"name": "Grace"})

contract.copy(update={"age": -5})
# SealFault — the override is validated, not trusted

# Defer validation when building a payload in stages
draft = contract.copy(update={"name": "Grace"}, validate=False)
final = draft.copy(update={"email": "g@example.com"})   # validates here

# Contracts with async wards
updated = await contract.copy_async(update={"sku": "ABC"})`}</CodeBlock>
      </section>

      {/* Data sources */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Alternate Data Sources</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Configuration gets the same validation as request data instead of a parallel parsing path. Every value arrives as a string; normal
          facet casting turns <code>&quot;8000&quot;</code> into an <code>int</code>:
        </p>
        <CodeBlock language="python">{`class SettingsContract(Contract):
    port = IntFacet(default=8000)
    database_url = TextFacet()

settings = SettingsContract.from_env(prefix="APP_")
# reads APP_PORT and APP_DATABASE_URL`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Absent variables are omitted rather than set empty, so each field&apos;s <code>default</code> and <code>required</code> rules decide the
          outcome exactly as they would for a JSON body. Validates by default, so configuration errors surface at startup rather than at first use.
        </p>
        <p className={`mt-6 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <code>from_cli()</code> parses <code>--flag value</code>, <code>--flag=value</code>, and bare <code>--flag</code>. Dashes map to
          underscores; a repeated flag collects into a list:
        </p>
        <CodeBlock language="python">{`class ImportContract(Contract):
    source = TextFacet()
    dry_run = BoolFacet(default=False)
    tags = ListFacet(child=TextFacet(), required=False)

options = ImportContract.from_cli(["--source", "data.csv", "--dry-run",
                                   "--tags", "a", "--tags", "b"])
# {"source": "data.csv", "dry_run": True, "tags": ["a", "b"]}`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Deliberately small: a parser for feeding a Contract, not a replacement for the <code>aq</code> CLI&apos;s Click layer. Unknown flags are
          ignored so a Contract can read the subset of arguments it cares about from a larger command line.
        </p>
        <p className={`mt-6 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Dataclasses, attrs classes, and <code>TypedDict</code> values are first-class Contract input at every level:
        </p>
        <CodeBlock language="python">{`from dataclasses import dataclass

@dataclass
class LineItemDTO:
    qty: int

Order(data={"items": [LineItemDTO(qty=3)]}).is_sealed()   # True`}</CodeBlock>
      </section>

      {/* i18n */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Localized Messages</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Every built-in validation message resolves through the active i18n catalog&apos;s <code>contracts.</code> namespace, falling back to the
          built-in English text with ICU-style <code>{'{name}'}</code> substitution:
        </p>
        <CodeBlock language="yaml">{`# locales/fr/messages.yaml
contracts:
  required: "Ce champ est obligatoire"
  min_length: "Doit contenir au moins {min} caractères"`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          The service and locale are read from context variables, so a request&apos;s locale applies to validation errors raised anywhere in its
          call tree without threading a locale parameter through every facet. Applications without i18n configured see byte-identical messages.
        </p>
        <div className={`mt-4 p-4 rounded-lg border ${t('bg-blue-500/5 border-blue-500/20','bg-blue-50 border-blue-200')}`}>
          <p className={`text-sm ${t('text-gray-300','text-gray-700')}`}>
            <strong className={t('text-blue-400','text-blue-700')}>Resolution never raises.</strong> A missing key, a malformed template, or a
            broken i18n service falls back to the built-in text. Failing to render the message for a rejected payload would turn a 422 into a 500,
            and the client would lose the validation errors entirely because of a translation problem.
          </p>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/contracts/async-pipeline" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Async Pipeline
        </Link>
        <Link to="/docs/contracts/projections" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Projections <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
