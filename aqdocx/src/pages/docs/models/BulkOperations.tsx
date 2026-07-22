import { useTheme } from '../../../context/ThemeContext';
import { CodeBlock } from '../../../components/CodeBlock';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NextSteps } from '../../../components/NextSteps';

export function BulkOperations() {
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
          <span className={t('text-gray-300', 'text-gray-600')}>Bulk Operations</span>
        </div>
        <h1 className={`text-4xl ${t('text-white', 'text-gray-900')}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Bulk Operations
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-xl mt-2 ${t('text-gray-300', 'text-gray-600')}`}>
          Efficient batch INSERT, bulk UPDATE, bulk DELETE, chunked iteration, and upsert patterns.
        </p>
      </div>

      {/* Signals warning */}
      <div className={`rounded-lg border p-4 text-sm mb-10 ${t('border-amber-500/20 bg-amber-500/5 text-amber-300', 'border-amber-300 bg-amber-50 text-amber-800')}`}>
        <strong>Signal behavior:</strong> <code>bulk_create()</code>, <code>.update()</code>, and <code>.delete()</code>
        do <strong>not</strong> fire <code>pre_save</code>, <code>post_save</code>, <code>pre_delete</code>, or <code>post_delete</code> signals.
        They operate directly at the SQL layer. Use instance-level <code>.save()</code> / <code>.delete_instance()</code> when signals are required.
      </div>

      {/* bulk_create */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}><code>bulk_create()</code></h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Inserts a list of model instances in one or more batched INSERT statements. Dramatically faster than
          calling <code>.save()</code> per instance for large datasets.
        </p>
        <CodeBlock language="python">
{`# Signature
async def bulk_create(
    db: AquiliaDatabase,
    objs: list[Model],
    batch_size: int = 1000,
) -> None

# Example: import 50,000 products
products = [
    Product(name=row['name'], price=row['price'], sku=row['sku'])
    for row in csv_rows
]
await Product.objects.bulk_create(db, products, batch_size=500)
# → Executes 100 INSERT statements, 500 rows each

# After bulk_create, PKs may or may not be assigned depending on backend.
# Re-query if you need the assigned IDs:
created = await Product.objects.filter(sku__in=[p.sku for p in products]).all()`}
        </CodeBlock>
        <div className={`mt-4 rounded-lg border p-4 text-sm ${t('border-blue-500/20 bg-blue-500/5 text-blue-300', 'border-blue-300 bg-blue-50 text-blue-800')}`}>
          <strong>batch_size guidance:</strong> SQLite has a default variable limit of 999 per statement.
          Keep <code>batch_size</code> at or below 999 for SQLite. PostgreSQL handles much larger batches efficiently.
          MySQL performs well at 500–5000 rows per batch depending on row width.
        </div>
      </section>

      {/* update */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}><code>.update()</code> — Bulk UPDATE</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Issues a single <code>UPDATE ... SET ... WHERE ...</code> statement for all rows matching the queryset filter.
          Accepts literal values, <code>F()</code> expressions, arithmetic, and <code>Case()</code> expressions.
        </p>
        <CodeBlock language="python">
{`# Signature
async def update(self, db: AquiliaDatabase, **kwargs) -> int  # returns rows affected

# Literal update — set all active users' role to 'member'
count = await User.objects.filter(is_active=True).update(db, role='member')

# F() expression — atomic increment (no Python read-modify-write)
await Product.objects.filter(id__in=popular_ids).update(db, views=F('views') + 1)

# Arithmetic on multiple fields
await Order.objects.filter(status='pending').update(
    db,
    total=F('subtotal') + F('tax'),
    updated_at=Now(),
)

# Conditional update with Case/When
from aquilia.models.expression import Case, When, Value
await Product.objects.update(
    db,
    status=Case(
        When(stock=0, then=Value('out_of_stock')),
        When(stock__lt=10, then=Value('low_stock')),
        default=Value('in_stock'),
    )
)

# Limit scope with filter
affected = await User.objects.filter(
    last_login__lt=cutoff_date
).update(db, is_active=False)`}
        </CodeBlock>
      </section>

      {/* delete */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}><code>.delete()</code> — Bulk DELETE</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Issues a single <code>DELETE FROM ... WHERE ...</code> for all rows matching the queryset. No signals fire.
        </p>
        <CodeBlock language="python">
{`# Signature
async def delete(self, db: AquiliaDatabase) -> int  # returns rows deleted

# Delete all expired sessions
deleted = await Session.objects.filter(expires_at__lt=now).delete(db)

# Delete with complex filter
await Log.objects.filter(
    created_at__lt=cutoff,
    level__in=['DEBUG', 'INFO'],
).delete(db)

# WARNING: .delete() with no filter deletes ALL rows in the table.
# Always verify your filter scope before calling .delete().`}
        </CodeBlock>
      </section>

      {/* in_bulk */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}><code>in_bulk()</code></h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Fetches a list of PKs and returns a <code>dict</code> mapping each PK to its model instance.
          Internally chunks large lists to avoid hitting SQLite's variable limit.
        </p>
        <CodeBlock language="python">
{`# Signature
async def in_bulk(
    self,
    id_list: list,
    batch_size: int = 999,
) -> dict[Any, Model]

# Fetch multiple users by ID without N+1
user_ids = [1, 5, 42, 99]
user_map = await User.objects.in_bulk(db, user_ids)
# → {1: <User id=1>, 5: <User id=5>, 42: <User id=42>, 99: <User id=99>}

alice = user_map[1]

# Large ID list — automatically chunked into batches of 999
all_ids = list(range(1, 50001))
product_map = await Product.objects.in_bulk(db, all_ids)
# → Makes ceil(50000/999) queries, merges results into one dict`}
        </CodeBlock>
      </section>

      {/* Upsert patterns */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Upsert Patterns</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Aquilia provides three methods for common get-or-create / upsert patterns. Understand their guarantees before choosing:
        </p>

        <div className={`rounded-lg border overflow-hidden mb-6 ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Method</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Creates?</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Updates?</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Race-safe?</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['get_or_create()', 'Yes', 'No', 'No — TOCTOU window'],
                ['update_or_create()', 'Yes', 'Yes', 'No — TOCTOU window'],
                ['find_or_create()', 'Yes', 'No', 'Yes — INSERT ON CONFLICT DO NOTHING'],
              ].map(([m, c, u, r]) => (
                <tr key={m as string}>
                  <td className={`px-4 py-3 font-mono ${t('text-aquilia-400', 'text-blue-600')}`}>{m}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{c}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{u}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{r}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className={`rounded-lg border p-4 text-sm mb-6 ${t('border-amber-500/20 bg-amber-500/5 text-amber-300', 'border-amber-300 bg-amber-50 text-amber-800')}`}>
          <strong>RuntimeWarning:</strong> <code>get_or_create()</code> and <code>update_or_create()</code> emit a
          <code> RuntimeWarning</code> on every call, since both are a plain SELECT-then-INSERT/UPDATE and not
          atomic under concurrent access. Prefer <code>find_or_create()</code> when a unique constraint is
          available — it does not warn.
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${t('text-gray-200', 'text-gray-800')}`}><code>get_or_create()</code></h3>
        <CodeBlock language="python">
{`# Returns (instance, created: bool)
user, created = await User.objects.get_or_create(
    db,
    defaults={'name': 'Alice', 'role': 'user'},
    email='alice@example.com',   # lookup fields
)
if created:
    print("New user created")
else:
    print("Existing user fetched")`}
        </CodeBlock>

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${t('text-gray-200', 'text-gray-800')}`}><code>update_or_create()</code></h3>
        <CodeBlock language="python">
{`# Returns (instance, created: bool)
# Updates existing row with defaults fields, or creates new row
profile, created = await Profile.objects.update_or_create(
    db,
    defaults={'bio': 'Updated bio', 'avatar': 'new.jpg'},
    user_id=42,   # lookup key
)`}
        </CodeBlock>

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${t('text-gray-200', 'text-gray-800')}`}><code>find_or_create()</code> — Atomic Upsert</h3>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Uses <code>INSERT ... ON CONFLICT DO NOTHING</code> under the hood, eliminating the TOCTOU race condition
          present in <code>get_or_create</code>. Safe under concurrent load without transactions.
        </p>
        <CodeBlock language="python">
{`# Returns (instance, created: bool)
tag, created = await Tag.objects.find_or_create(
    db,
    defaults={'color': '#ff0000'},
    create_defaults={'slug': 'python'},
    name='Python',   # lookup + unique constraint field
)
# Under the hood:
# INSERT INTO "tags" ("name", "color", "slug")
# VALUES (?, ?, ?) ON CONFLICT DO NOTHING
# Then SELECT to return the row regardless of insert vs conflict`}
        </CodeBlock>
      </section>

      {/* iterator */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}><code>.iterator()</code> — Memory-Efficient Chunked Iteration</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          <code>.iterator()</code> returns an async generator that fetches and yields rows in chunks.
          Unlike <code>.all()</code>, it does not load the entire result set into memory at once — essential for
          processing hundreds of thousands of rows.
        </p>
        <CodeBlock language="python">
{`# Signature
def iterator(self, chunk_size: int = 2000) -> AsyncGenerator[Model, None]

# Process 1M rows without OOM
async for user in User.objects.filter(is_active=True).iterator(chunk_size=500):
    await process_user(user)

# With ordering — ensures consistent chunking
async for order in Order.objects.order('id').iterator():
    await send_receipt(order)

# Cannot use .all() or .first() after .iterator() — it is a terminal method
# Cannot slice or further chain after calling .iterator()`}
        </CodeBlock>
      </section>

      {/* select_for_update */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}><code>select_for_update()</code></h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Adds <code>SELECT ... FOR UPDATE</code> locking to the query. Must be used inside an <code>atomic()</code> block.
          Not supported on SQLite (raises <code>QueryFault</code> on SQLite).
        </p>
        <CodeBlock language="python">
{`# Signature
def select_for_update(
    self,
    nowait: bool = False,
    skip_locked: bool = False,
) -> QuerySet

from aquilia.models import atomic

async with atomic(db):
    # Lock the row for the duration of the transaction
    account = await (
        BankAccount.objects
        .filter(id=account_id)
        .select_for_update()
        .first()
    )
    account.balance -= amount
    await account.save(db)

# nowait=True → raises immediately if row is locked (no waiting)
async with atomic(db):
    try:
        job = await Job.objects.filter(status='pending').select_for_update(nowait=True).first()
    except Exception:
        return  # Another worker has it

# skip_locked=True → skips locked rows (queue worker pattern)
async with atomic(db):
    job = await (
        Job.objects
        .filter(status='pending')
        .select_for_update(skip_locked=True)
        .order('created_at')
        .first()
    )
    if job:
        await process_job(job)`}
        </CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700', 'border-gray-200')}`}>
        <Link
          to="/docs/models/recursive-cte"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          <ArrowLeft className="w-4 h-4" /> Recursive CTEs
        </Link>
        <Link
          to="/docs/models/advanced"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          Advanced Usage <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  );
}
