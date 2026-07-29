import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ContractsAsyncPipeline() {
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
        <span className={t('text-gray-300','text-gray-600')}>Async Pipeline</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Async Pipeline</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Validating with awaited rules, and serializing models whose relations are async.
        </p>
      </div>

      {/* Async wards */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Async Wards</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          A validator that needs to await declares <code>mode=&quot;async&quot;</code>. Mode is explicit rather than inferred, so a rule
          written as a sync <code>def</code> that awaits cannot silently register as synchronous:
        </p>
        <CodeBlock language="python">{`from aquilia.contracts import Contract, ward
from aquilia.contracts.facets import EmailFacet

class UserContract(Contract):
    email = EmailFacet()

    @ward(mode="async")
    async def email_unique(self, data):
        if await User.objects.filter(email=data["email"]).exists():
            self.reject("email", "Email address is already registered")`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Run them with <DocTerm id="bp.is_sealed">is_sealed_async()</DocTerm>:
        </p>
        <CodeBlock language="python">{`if not await contract.is_sealed_async():
    return Response.json(contract.errors, status=422)`}</CodeBlock>
      </section>

      {/* Mismatch */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Calling the Wrong Entry Point</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Calling the synchronous <code>is_sealed()</code> on a Contract with async wards raises rather than skipping them:
        </p>
        <CodeBlock language="python">{`contract.is_sealed()
# ContractAsyncMismatchFault (BP201): Contract contains async wards and must be
# validated using is_sealed_async().`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <code>has_async_wards</code> reports whether the async entry point is required. As of v1.3.5 it walks nested Contracts, so a parent
          whose <em>child</em> declares an async ward is correctly detected:
        </p>
        <CodeBlock language="python">{`class Child(Contract):
    sku = TextFacet()

    @ward(mode="async")
    async def in_stock(self, data): ...

class Parent(Contract):
    items: list[Child] = None

Parent(data={}).has_async_wards   # True`}</CodeBlock>
        <div className={`mt-4 p-4 rounded-lg border ${t('bg-amber-500/5 border-amber-500/20','bg-amber-50 border-amber-200')}`}>
          <p className={`text-sm ${t('text-gray-300','text-gray-700')}`}>
            <strong className={t('text-amber-400','text-amber-700')}>Changed in v1.3.5.</strong> This previously reported <code>False</code> for a
            nested async ward, so callers took the sync path and the ward never ran — a silent skip rather than the intended fault. The walk is
            memoized per class, with cycle detection for self-referential Contracts.
          </p>
        </div>
      </section>

      {/* Async serialization */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Async Serialization</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Aquilia&apos;s ORM relations are async, so serializing a model with an un-awaited relation has to await it. Two entry points mirror the
          synchronous ones:
        </p>
        <CodeBlock language="python">{`# Single instance
data = await OrderContract.to_dict_async(order)

# Collection
rows = await OrderContract.to_dict_many_async(orders)`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <DocTerm id="bp.lens">Lens</DocTerm> resolves its relation through <code>mold_async()</code>, so prefetching becomes an optimization
          rather than a requirement:
        </p>
        <CodeBlock language="python">{`class OrderContract(Contract):
    items = Lens(ItemContract, many=True)

order = await Order.objects.get(pk=1)          # items not prefetched
data = await OrderContract.to_dict_async(order)  # awaits order.items`}</CodeBlock>
      </section>

      {/* Unresolved relations */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Unresolved Relations on the Sync Path</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          The synchronous path cannot await, so an un-awaited related manager raises <code>LensUnresolvedFault</code> (<code>BP503</code>)
          naming the field:
        </p>
        <CodeBlock language="python">{`order = await Order.objects.get(pk=1)   # items NOT prefetched
OrderContract(instance=order).data
# LensUnresolvedFault`}</CodeBlock>
        <p className={`mt-4 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>Three ways to resolve it:</p>
        <CodeBlock language="python">{`# 1. Prefetch — best for hot paths
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).data

# 2. Materialize explicitly
order.items = await order.items.all()
OrderContract(instance=order).data

# 3. Use the async serializer, which awaits for you
await OrderContract.to_dict_async(order)`}</CodeBlock>
        <div className={`mt-4 p-4 rounded-lg border ${t('bg-amber-500/5 border-amber-500/20','bg-amber-50 border-amber-200')}`}>
          <p className={`text-sm ${t('text-gray-300','text-gray-700')}`}>
            <strong className={t('text-amber-400','text-amber-700')}>Changed in v1.3.5.</strong> This previously returned an empty list, which is
            indistinguishable from &quot;this record genuinely has no related rows&quot; — silently shipping wrong data to clients. Failing loudly
            at development time is the safer default.
          </p>
        </div>
      </section>

      {/* Performance */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Performance Notes</h2>
        <ul className={`space-y-2 text-sm list-disc pl-5 ${t('text-gray-300','text-gray-600')}`}>
          <li><strong>Prefetching is still the right choice on hot paths.</strong> <code>to_dict_async()</code> awaits relations sequentially, issuing one query per un-prefetched relation. It exists so a missing prefetch costs a query rather than raising.</li>
          <li><strong>Awaiting already-materialized data is close to free</strong>, so the async path is not slower than the sync path for prefetched models.</li>
          <li><strong>Bulk async validation is sequential per item.</strong> Unbounded concurrency over a 10,000-item batch would exhaust the database connection pool.</li>
          <li><strong>Sync and async share one field-molding generator</strong>, so projections, <code>write_only</code> exclusion, and computed fields cannot drift between the two implementations.</li>
        </ul>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/contracts/seals" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Seals & Validation
        </Link>
        <Link to="/docs/contracts/validation-control" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Validation Control <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
