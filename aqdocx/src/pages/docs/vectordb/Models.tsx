import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Layers, AlertTriangle, CheckCircle2 } from 'lucide-react'

const annotations: [string, string][] = [
  ['Key()', 'Primary key. Natural keys ("post:42") fold to a deterministic UUID, so get() finds what save() wrote.'],
  ['Text()', 'Source text for embedding. A model with one text field embeds on write and on query.'],
  ['Dimension(n)', 'Marks the vector field and fixes its length. Must match the store dimension.'],
  ['Payload(name=..., indexed=...)', 'Metadata stored alongside the vector. name overrides the on-disk key; indexed is recorded for a future metadata index and is not yet acted on.'],
  ['Score()', 'Read-only field receiving a search hit score. Stays None outside a query, and is never written.'],
  ['MinLength / MaxLength', 'String bounds, enforced by validate() before a write.'],
  ['MinValue / MaxValue / Range', 'Numeric bounds.'],
  ['Pattern / Email / URL / Slug', 'Regex-backed string shapes.'],
  ['Choices(*values)', 'Restricts a payload value to a fixed set. Takes varargs, not a list.'],
  ['Validate(fn)', 'Arbitrary callable predicate for anything the built-ins do not cover.'],
]

export function VectorDBModels() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4 animate-pulse" />
          Vector Database / Models
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Vector Models
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          A <code className="text-aquilia-500">VectorModel</code> describes one collection. Field
          roles come from <code className="text-aquilia-500">Annotated</code> metadata rather than
          custom field objects, so a model stays a readable dataclass-shaped declaration and type
          checkers still see the real Python types.
        </p>
      </div>

      {/* Anatomy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Anatomy of a model
        </h2>
        <CodeBlock language="python" highlightLines={[6, 7, 8, 9, 10, 13, 14, 15]}>{`from typing import Annotated
from aquilia.vectordb import (
    VectorModel, Key, Text, Payload, Dimension, Score, MaxLength, MinValue, Choices,
)

class Article(VectorModel):
    key:     Annotated[str, Key()]
    title:   Annotated[str, Payload(), MaxLength(200)]
    body:    Annotated[str, Text()]
    vector:  Annotated[list[float], Dimension(384)]
    kind:    Annotated[str, Payload(), Choices("post", "doc", "faq")]
    views:   Annotated[int, Payload(), MinValue(0)]
    score:   Annotated[float | None, Score()] = None

    class Meta:
        collection = "articles"
        store = "default"`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          <code className="text-aquilia-500">Meta.collection</code> names the collection;{' '}
          <code className="text-aquilia-500">Meta.store</code> selects the store alias declared on
          the workspace. Read the resolved values with{' '}
          <code className="text-aquilia-500">Article.collection_name()</code>,{' '}
          <code className="text-aquilia-500">Article.schema()</code> and{' '}
          <code className="text-aquilia-500">Article.options()</code>.
        </p>
      </section>

      {/* Annotation reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Annotation reference
        </h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-60">Annotation</th>
                <th className="text-left py-4 px-6 font-semibold">Meaning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {annotations.map(([name, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400">{name}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Instance lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Instance lifecycle
        </h2>
        <CodeBlock language="python" highlightLines={[4, 11, 14, 17]}>{`article = Article(key="post:42", title="Ship it", body="Long text...", kind="post", views=0)

# validate() runs on save; call it early if you want the fault sooner
article.validate()

# Embeds from \`body\` when: no vector set, a text field exists, embedder reachable.
# Pass embed=False to store exactly the vector you supplied.
await article.save()
await article.save(embed=False)

# Re-read the stored state (vector included) into this instance
await article.refresh()

# Remove just this record
await article.delete_instance()

# Serialise; the vector is omitted unless asked for
article.to_dict(include_vector=True)`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          Signals fire around writes:{' '}
          <code className="text-aquilia-500">vector_pre_save</code>,{' '}
          <code className="text-aquilia-500">vector_post_save</code>,{' '}
          <code className="text-aquilia-500">vector_pre_delete</code>,{' '}
          <code className="text-aquilia-500">vector_post_delete</code>, plus{' '}
          <code className="text-aquilia-500">vector_class_prepared</code> when the metaclass finishes
          building a model.
        </p>
      </section>

      {/* Common mistakes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          Common mistakes
        </h2>
        <div className="space-y-4">
          {[
            [
              'Dimension disagrees with the store',
              'Dimension(768) on a model whose store declares 384 raises VectorDimensionFault at first write. Keep one constant and reference it from both.',
            ],
            [
              'Assuming Payload(indexed=True) speeds up a filter',
              'elips filters scan metadata linearly today. The flag is recorded for a future metadata index but is not yet acted on, so it changes nothing about how a predicate executes.',
            ],
            [
              'Renaming a payload attribute without Payload(name=...)',
              'The metadata key defaults to the attribute name, so a rename orphans existing data. Pin the on-disk key with Payload(name="old_name").',
            ],
            [
              'Expecting text search with no text field',
              'search(text=...) needs a Text() field and a store embedder. Without either, pass vector= yourself.',
            ],
            [
              'Two models, same collection, different schemas',
              'The collection is keyed by name. Two disagreeing declarations race on the same data; give them separate collections.',
            ],
          ].map(([title, body], i) => (
            <div key={i} className={`rounded-xl border p-5 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
              <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Best practice */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          Best practice
        </h2>
        <CodeBlock language="python">{`# Share the dimension between the model and the store config
EMBED_DIM = 384

class Article(VectorModel):
    key:    Annotated[str, Key()]
    body:   Annotated[str, Text()]
    vector: Annotated[list[float], Dimension(EMBED_DIM)]

# workspace.py
VectorStoreConfig(alias="default", dimension=EMBED_DIM, metric="cosine")`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
