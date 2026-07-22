import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function DefiningRelationships() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <Link to="/docs/models/overview" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Models</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Defining Relationships</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Defining Relationships</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Aquilia ORM supports first-class relational fields including Many-to-One, One-to-One, and Many-to-Many configurations.
        </p>
      </div>

      {/* ForeignKey */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>ForeignKey (Many-to-One)</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Declares a many-to-one relationship. Requires the target model (either class reference or forward reference string) and <code>on_delete</code> behavior:
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import ForeignKey

class Post(Model):
    # Class reference
    author = ForeignKey(User, on_delete="CASCADE", related_name="posts")
    
    # Or string reference (prevents circular imports)
    category = ForeignKey("Category", on_delete="SET_NULL", null=True)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${t('text-white','text-gray-900')}`}>On-Delete Actions</h3>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Supported database-level delete cascades:
        </p>
        <ul className={`list-disc list-inside space-y-2 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <li><code>"CASCADE"</code>: Cascades the deletion of the referenced row to this row.</li>
          <li><code>"SET_NULL"</code>: Sets the foreign key column to NULL (requires <code>null=True</code>).</li>
          <li><code>"RESTRICT"</code>: Rejects parent deletion if dependent children rows exist.</li>
          <li><code>"SET_DEFAULT"</code>: Sets the column to its configured default value.</li>
          <li><code>"DO_NOTHING"</code>: No database-level action is taken (raw foreign key remains unchanged).</li>
        </ul>
      </section>

      {/* OneToOneField */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>OneToOneField</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Similar to <code>ForeignKey</code>, but enforces a UNIQUE constraint on the foreign key column, establishing a strict 1-to-1 link:
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import OneToOneField

class Profile(Model):
    user = OneToOneField(User, on_delete="CASCADE", related_name="profile")`}</CodeBlock>
      </section>

      {/* ManyToManyField */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>ManyToManyField</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Configures a many-to-many relationship. Automatically generates an intermediary junction table:
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import ManyToManyField

class Article(Model):
    tags = ManyToManyField("Tag", related_name="articles")`}</CodeBlock>
      </section>

      {/* GenericForeignKey */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>GenericForeignKey</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          A polymorphic relation to <em>any</em> registered model — Django's "virtual field" pattern. Unlike
          <code> ForeignKey</code>, it doesn't own a database column of its own: you declare two real columns
          yourself (a model-label column and a stringified-PK column), and <code>GenericForeignKey</code>
          resolves between them.
        </p>
        <CodeBlock language="python">{`from aquilia.models import Model, AutoField, CharField, GenericForeignKey

class Comment(Model):
    id = AutoField(primary_key=True)
    body = CharField(max_length=1000)
    content_type = CharField(max_length=255)   # e.g. "User", "Post", "Ticket"
    object_id = CharField(max_length=255)      # stringified PK -- works for int or UUID PKs
    target = GenericForeignKey("content_type", "object_id")`}</CodeBlock>
        <CodeBlock language="python">{`post = await Post.get(pk=1)
comment = Comment(body="Nice post!")
Comment.target.attach(comment, post)   # sets content_type="Post", object_id=str(post.pk)
await comment.save()

# ... later, after loading a row back from the DB:
reloaded = await Comment.get(pk=comment.pk)
target = await Comment.target.resolve(reloaded)   # -> the Post instance, or None`}</CodeBlock>
        <p className={`mb-3 mt-6 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <strong>Why an explicit async method, not a transparent attribute:</strong> Aquilia is async-native —
          there's no way to do a lazy synchronous DB fetch on plain attribute access the way Django's sync ORM
          can. Resolution is always <code>await field.resolve(instance)</code>.
        </p>
        <p className={`mb-3 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <strong>Why no ContentType model:</strong> Django's <code>GenericForeignKey</code> looks up a
          <code> content_type_id</code> against a database-backed <code>ContentType</code> table. Aquilia reuses
          the already-existing, in-memory <code>ModelRegistry.get(label)</code> lookup — the same primitive
          <code> ForeignKey</code> already uses for string-based relation resolution — so no extra table,
          migration, or registry sync step is needed.
        </p>
        <p className={`text-sm ${t('text-gray-300','text-gray-600')}`}>
          Not a <code>Field</code> subclass — the metaclass's column-collection scan skips it entirely, so it
          owns no schema column and doesn't appear in generated <code>CREATE TABLE</code> DDL. An unset target
          resolves to <code>None</code>, not an error.
        </p>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/queryset" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> QuerySet API
        </Link>
        <Link to="/docs/models/relationships/hydration" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Hydration Primitives <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
