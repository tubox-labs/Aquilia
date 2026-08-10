import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Link2, AlertTriangle } from 'lucide-react'

export function VectorDBInterop() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  const card = (title: string, body: React.ReactNode) => (
    <div className={`rounded-xl border p-5 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
      <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</h3>
      <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{body}</p>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Link2 className="w-4 h-4 animate-pulse" />
          Vector Database / SQL Interop
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Working With the SQL ORM
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Vectors and rows live in different stores. Aquilia does not pretend otherwise — there is no
          join, no foreign key and no cascade across the boundary. What it gives you instead is an
          explicit link, a one-query hydration helper, and a mirror that keeps the two in step.
        </p>
      </div>

      {/* Link */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Link: a pointer, not a foreign key
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          <code className="text-aquilia-500">Link</code> marks a payload attribute as holding a SQL
          primary key. It compiles to an ordinary payload entry plus registry metadata naming the
          target model. elips has no referential integrity, so the name avoids implying one.
        </p>
        <CodeBlock language="python" highlightLines={[8, 14]}>{`from typing import Annotated
from aquilia.vectordb import VectorModel, Key, Text, Link, resolve
from myapp.models import User

class Document(VectorModel):
    key:     Annotated[str, Key()]
    body:    Annotated[str, Text()]
    user_id: Annotated[int, Link(User)]

hit = (await Document.vectors.search("alpha"))[0]

# One SELECT, and you can see it happen
user = await resolve(hit, "user_id")`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          <code className="text-aquilia-500">on_delete</code> takes{' '}
          <code className="text-aquilia-500">&quot;detach&quot;</code> (default — the vector record
          survives with a link pointing at nothing) or{' '}
          <code className="text-aquilia-500">&quot;purge&quot;</code>. It is honoured only when the
          SQL model is mirrored. There is deliberately no{' '}
          <code className="text-aquilia-500">&quot;cascade&quot;</code> spelling: that word would
          promise a database-level guarantee this boundary cannot make. Pass a dotted{' '}
          <code className="text-aquilia-500">&quot;module:Class&quot;</code> string for a forward
          reference.
        </p>
      </section>

      {/* as_models */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Hybrid retrieval with as_models()
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          The common shape: rank by similarity, return fully-loaded SQL rows. Collect primary keys
          from the hits, fetch them in one <code className="text-aquilia-500">pk__in</code> query,
          then re-sort into relevance order — because SQL <code className="text-aquilia-500">IN</code>{' '}
          does not preserve argument order, and relevance ordering is the entire point.
        </p>
        <CodeBlock language="python" highlightLines={[4, 5, 6, 7]}>{`from aquilia.vectordb import as_models

hits = await Document.vectors.search("alpha design", limit=20)
posts = await as_models(
    hits, Post, via="post_id",
    queryset=Post.query().select_related("author"),
)

# Need the score alongside the row
pairs = await as_models(hits, Post, via="post_id", with_hits=True)
for post, hit in pairs:
    print(hit.score, post.title)`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          One round trip, not N+1. Keys are chunked at{' '}
          <code className="text-aquilia-500">PK_CHUNK_SIZE</code> to respect the SQLite parameter
          ceiling. Several chunks of one document pointing at the same row deduplicate to one row at
          its best position, and rows the SQL side no longer has are dropped rather than yielding{' '}
          <code className="text-aquilia-500">None</code> holes.
        </p>
      </section>

      {/* mirror */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Keeping the two in sync with @mirror
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          <code className="text-aquilia-500">@mirror</code> registers{' '}
          <code className="text-aquilia-500">post_save</code> /{' '}
          <code className="text-aquilia-500">post_delete</code> handlers on the existing{' '}
          <code className="text-aquilia-500">aquilia.models.signals</code> bus, so a SQL write keeps
          the vector collection current.
        </p>
        <CodeBlock language="python" highlightLines={[3, 4, 5, 6, 7, 8]}>{`from aquilia.vectordb import mirror

@mirror(
    into=Document,
    text=lambda p: f"{p.title}\\n\\n{p.body}",
    meta={"kind": "post", "author_id": lambda p: p.author_id},
    when=lambda p: p.published,
    on_delete="purge",
)
class Post(Model):
    ...`}</CodeBlock>
        <div className="mt-6 space-y-4">
          {card(
            'Queued by default, and that matters',
            <>
              <code className="text-aquilia-500">sync=&quot;task&quot;</code> (default) enqueues the
              write through <code className="text-aquilia-500">aquilia.tasks</code>. A vector write
              inside a request transaction adds embedding latency to the response and cannot roll
              back with the SQL transaction, so a rolled-back save would leave an orphaned vector
              record. <code className="text-aquilia-500">sync=&quot;inline&quot;</code> exists for
              tests and small scripts where a background worker is overkill.
            </>,
          )}
          {card(
            'when= removes as well as skips',
            <>
              An instance failing the predicate is skipped <em>and</em> any existing vector record
              for it is removed. Un-publishing a post takes it out of the index rather than leaving
              a stale copy that keeps ranking.
            </>,
          )}
          {card(
            'text= or vector=, one of the two',
            <>
              <code className="text-aquilia-500">text=</code> builds the string to embed;{' '}
              <code className="text-aquilia-500">vector=</code> supplies the vector directly and
              bypasses embedding entirely. <code className="text-aquilia-500">key=</code> defaults to{' '}
              <code className="text-aquilia-500">&quot;&lt;table&gt;:&lt;pk&gt;&quot;</code>.
            </>,
          )}
        </div>
      </section>

      {/* bulk blind spot */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          The bulk_create blind spot
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          <code className="text-aquilia-500">bulk_create()</code> and{' '}
          <code className="text-aquilia-500">bulk_update()</code> fire no signals, so rows written
          that way never reach the mirror. This is a real gap, documented rather than papered over,
          and <code className="text-aquilia-500">reindex()</code> is the repair.
        </p>
        <CodeBlock language="python" highlightLines={[6]}>{`from aquilia.vectordb import reindex

await Post.bulk_create(rows)     # no signals fired — mirror does not see these

# Rebuild the mirrored collection from the SQL table
written = await reindex(Post, batch_size=500)`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          Or from the shell: <code className="text-aquilia-500">aq vectordb reindex Post</code>.
          Reindexing a model with no registered mirror raises{' '}
          <code className="text-aquilia-500">VectorRegistryFault</code> rather than silently doing
          nothing. Run it against a stopped app — it takes the writer lock.
        </p>
      </section>

      <NextSteps />
    </div>
  )
}
