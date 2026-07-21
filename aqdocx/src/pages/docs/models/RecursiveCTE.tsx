import { useTheme } from '../../../context/ThemeContext';
import { CodeBlock } from '../../../components/CodeBlock';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NextSteps } from '../../../components/NextSteps';

export function RecursiveCTE() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const t = (dark: string, light: string) => isDark ? dark : light;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm mb-4">
          <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
          <span className={t('text-gray-500', 'text-gray-400')}>/</span>
          <Link to="/docs/models/overview" className={t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}>Models</Link>
          <span className={t('text-gray-500', 'text-gray-400')}>/</span>
          <span className={t('text-gray-300', 'text-gray-600')}>Recursive CTEs</span>
        </div>
        <h1 className={`text-4xl ${t('text-white', 'text-gray-900')}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Recursive CTEs
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-xl mt-2 ${t('text-gray-300', 'text-gray-600')}`}>
          Traverse hierarchical and graph data in pure SQL — folder trees, org charts, dependency graphs.
        </p>
        <div className={`mt-3 inline-flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full border ${t('border-aquilia-500/30 bg-aquilia-500/10 text-aquilia-400', 'border-aquilia-500/40 bg-aquilia-50 text-aquilia-600')}`}>
          v1.3.3+
        </div>
      </div>

      {/* Concept */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Concept</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          A <strong>recursive CTE</strong> uses the <code>WITH RECURSIVE</code> keyword and consists of two parts joined by <code>UNION ALL</code> (or <code>UNION</code>):
        </p>
        <ol className={`list-decimal ml-6 mb-4 space-y-2 ${t('text-gray-300', 'text-gray-600')}`}>
          <li><strong>Anchor term</strong> — the base query, run once, producing initial rows (e.g., root nodes)</li>
          <li><strong>Recursive term</strong> — references the CTE itself to join against previous iteration results, expanding outward</li>
        </ol>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          The database engine iterates until the recursive term produces no new rows.
        </p>
        <div className={`rounded-lg border p-4 text-sm ${t('border-amber-500/20 bg-amber-500/5 text-amber-300', 'border-amber-300 bg-amber-50 text-amber-800')}`}>
          <strong>Warning:</strong> Without a termination condition, recursive CTEs can loop infinitely on cyclic graphs.
          Use <code>UNION</code> (not <code>UNION ALL</code>) to deduplicate and prevent cycles, or add a depth counter and filter it in the anchor or application layer.
        </div>
      </section>

      {/* API */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>API: <code>Q.recursive_cte()</code></h2>
        <div className={`rounded-lg border overflow-hidden mb-4 ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Parameter</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Type</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['name', 'str', 'CTE name — valid SQL identifier (a-z, A-Z, 0-9, _).'],
                ['anchor', '(Q) -> Q', 'Lambda receiving a fresh QuerySet, returns the base / non-recursive term.'],
                ['recursive', '(CTEReference) -> Q', 'Lambda receiving CTEReference, returns the recursive term. Use cte_ref.col("field") to reference CTE columns.'],
                ['union_all', 'bool', 'True (default) = UNION ALL (no dedup, faster). False = UNION (deduplicates, safe for cyclic graphs).'],
              ].map(([p, type, desc]) => (
                <tr key={p}>
                  <td className={`px-4 py-3 font-mono ${t('text-aquilia-400', 'text-blue-600')}`}>{p}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400', 'text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          <code>.recursive_cte()</code> returns a new QuerySet that selects <code>FROM</code> the named CTE table and carries the
          <code>RecursiveCTE</code> in its WITH RECURSIVE clause. Terminal methods (<code>.all()</code>, <code>.first()</code>) execute the full query.
        </p>
      </section>

      {/* Folder Tree */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Example: Folder Tree Traversal</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          A self-referential <code>Folder</code> model with a <code>parent_id</code> nullable FK to itself.
        </p>
        <CodeBlock language="python">
{`class Folder(Model):
    table = "folders"
    name = CharField(max_length=255)
    parent_id = IntegerField(null=True)   # FK to folders.id

# Fetch entire subtree rooted at parent_id IS NULL (top-level)
all_folders = await Folder.objects.recursive_cte(
    name='folder_tree',
    anchor=lambda q: q.filter(parent_id__isnull=True),        # Root nodes
    recursive=lambda cte: Folder.objects.filter(
        parent_id=cte.col('id')                                # Children of previous level
    ),
    union_all=True,   # Trees have no cycles — UNION ALL is faster
).all()

# Generates:
# WITH RECURSIVE "folder_tree" AS (
#     SELECT * FROM "folders" WHERE "parent_id" IS NULL          -- anchor
#     UNION ALL
#     SELECT f.* FROM "folders" f
#     INNER JOIN "folder_tree" ft ON f."parent_id" = ft."id"     -- recursive
# )
# SELECT * FROM "folder_tree"`}
        </CodeBlock>
      </section>

      {/* Org Chart */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Example: Org Chart (All Reports Under a Manager)</h2>
        <CodeBlock language="python">
{`class Employee(Model):
    table = "employees"
    name = CharField(max_length=255)
    manager_id = IntegerField(null=True)   # FK to employees.id

async def all_reports(manager_id: int) -> list[Employee]:
    """Return the manager and all their direct/indirect reports."""
    return await Employee.objects.recursive_cte(
        name='reports',
        anchor=lambda q: q.filter(id=manager_id),         # Start node
        recursive=lambda cte: Employee.objects.filter(
            manager_id=cte.col('id')
        ),
        union_all=True,
    ).all()`}
        </CodeBlock>
      </section>

      {/* Dependency Graph */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Example: Dependency Graph (UNION for Cycle Safety)</h2>
        <CodeBlock language="python">
{`class Package(Model):
    table = "packages"
    name = CharField(max_length=255)

class PackageDep(Model):
    table = "package_deps"
    package_id = IntegerField()
    depends_on_id = IntegerField()

# Resolve all transitive dependencies of a given package
async def transitive_deps(package_id: int) -> list[Package]:
    return await Package.objects.recursive_cte(
        name='dep_tree',
        anchor=lambda q: q.filter(id=package_id),
        recursive=lambda cte: Package.objects.filter(
            packagedep__package_id=cte.col('id')
        ),
        union_all=False,   # UNION — deduplicates, prevents infinite loops on diamond deps
    ).all()`}
        </CodeBlock>
      </section>

      {/* UNION vs UNION ALL */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>UNION vs UNION ALL</h2>
        <div className={`rounded-lg border overflow-hidden ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Setting</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>SQL</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>When to use</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['union_all=True (default)', 'UNION ALL', 'Trees and DAGs with no cycles. Faster — no deduplication overhead.'],
                ['union_all=False', 'UNION', 'Graphs that may have cycles or diamond paths. Terminates via deduplication.'],
              ].map(([s, sql, when]) => (
                <tr key={s as string}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400', 'text-blue-600')}`}>{s}</td>
                  <td className={`px-4 py-3 font-mono ${t('text-gray-400', 'text-gray-500')}`}>{sql}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{when}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* CTEReference */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>CTEReference and <code>cte.col()</code></h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Inside the <code>recursive</code> lambda, the argument is a <code>CTEReference</code>. Call <code>.col("column")</code>
          on it to produce a <code>CTECol</code> expression that renders as <code>"cte_name"."column"</code> in SQL.
        </p>
        <CodeBlock language="python">
{`lambda cte: Folder.objects.filter(parent_id=cte.col('id'))
# cte.col('id') → CTECol("folder_tree", "id")
# Renders as: "folders"."parent_id" = "folder_tree"."id"`}
        </CodeBlock>
      </section>

      {/* Performance */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Performance Considerations</h2>
        <ul className={`space-y-3 ${t('text-gray-300', 'text-gray-600')}`}>
          <li className="flex gap-3">
            <span className="text-blue-400 mt-0.5">ℹ</span>
            <span><strong>Index parent_id</strong> — the recursive join hits <code>parent_id</code> on every iteration. Missing index causes full table scan per level.</span>
          </li>
          <li className="flex gap-3">
            <span className="text-blue-400 mt-0.5">ℹ</span>
            <span><strong>Depth-limit via counter</strong> — add a <code>depth</code> annotation in the anchor (initialized to 0 via <code>Value(0)</code>) and increment in the recursive term to limit traversal depth.</span>
          </li>
          <li className="flex gap-3">
            <span className="text-amber-400 mt-0.5">⚠</span>
            <span><strong>Large result sets</strong> — recursive CTEs materialize all levels before returning. For very deep trees, combine with <code>.limit()</code> or use a depth counter.</span>
          </li>
          <li className="flex gap-3">
            <span className="text-green-400 mt-0.5">✓</span>
            <span><strong>Use <code>.explain()</code></strong> — <code>await Folder.objects.recursive_cte(...).explain()</code> shows the query plan including CTE materialization strategy.</span>
          </li>
        </ul>
      </section>

      {/* Backend Compat */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Backend Compatibility</h2>
        <div className={`rounded-lg border overflow-hidden ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Backend</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Min Version</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Notes</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['SQLite', '3.8.3+', 'WITH RECURSIVE fully supported.'],
                ['PostgreSQL', '8.4+', 'Full recursive CTE with UNION / UNION ALL.'],
                ['MySQL', '8.0+', 'WITH RECURSIVE supported. MySQL < 8.0 has no CTE support at all.'],
              ].map(([b, v, n]) => (
                <tr key={b as string}>
                  <td className={`px-4 py-3 font-semibold ${t('text-gray-200', 'text-gray-800')}`}>{b}</td>
                  <td className={`px-4 py-3 font-mono ${t('text-gray-400', 'text-gray-500')}`}>{v}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700', 'border-gray-200')}`}>
        <Link
          to="/docs/models/cte"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          <ArrowLeft className="w-4 h-4" /> Common Table Expressions
        </Link>
        <Link
          to="/docs/models/bulk-operations"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          Bulk Operations <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  );
}
