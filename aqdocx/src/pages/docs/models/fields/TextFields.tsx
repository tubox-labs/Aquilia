import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function TextFields() {
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
        <span className={t('text-gray-300','text-gray-600')}>Text Fields</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Text & String Fields</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Expressive text fields with bounds validation, email formatting, case-insensitivity checks, and URL patterns.
        </p>
      </div>

      {/* Fields list */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Field Catalogue</h2>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Field</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>SQL (SQLite / Postgres)</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['CharField', 'VARCHAR(n)', 'Text field with maximum length constraint.'],
                ['TextField', 'TEXT', 'Unlimited text field (usually aliased CharField with max_length=None).'],
                ['EmailField', 'VARCHAR(254)', 'Validates email formats.'],
                ['URLField', 'VARCHAR(2048)', 'Validates URL formats.'],
                ['SlugField', 'VARCHAR(50)', 'Accepts slugs (lowercase letters, numbers, hyphens).'],
                ['EncryptedField', 'TEXT', 'Transparently encrypted at the storage boundary (see below).'],
              ].map(([f, sql, desc]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{sql}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Case Insensitive Fields */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Case-Insensitive (CI) Fields</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Aquilia supports first-class case-insensitive lookups via <code>CICharField</code>, <code>CIEmailField</code>, and <code>CITextField</code>. Perfect for user lookups:
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import CICharField, CIEmailField

class User(Model):
    username = CICharField(max_length=50, unique=True)
    email = CIEmailField(unique=True)`}</CodeBlock>
      </section>

      {/* Encrypted Fields */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>EncryptedField</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Transparent application-layer encryption at the storage boundary. Plaintext is validated as a normal
          <code> TextField</code> on assignment; encryption/decryption happens only in <code>to_db()</code>/
          <code>to_python()</code> — i.e. only on the wire to/from the database.
        </p>
        <CodeBlock language="python">{`import os
from aquilia.models import Model, EncryptedField

# Configure once, at app startup -- before any encrypted field is saved/read.
EncryptedField.configure_encryption_key(os.environ["ENCRYPTION_KEY"])

class User(Model):
    email = CharField(max_length=255, unique=True)
    ssn = EncryptedField(null=True)

user = await User.create(email="a@test.com", ssn="123-45-6789")
# The "ssn" column holds ciphertext, not plaintext.

reloaded = await User.get(pk=user.pk)
reloaded.ssn  # "123-45-6789" -- decrypted transparently on read`}</CodeBlock>
        <p className={`mb-3 mt-6 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Encryption backend priority: a custom callable pair via <code>configure_encryption()</code>, then
          Fernet (if the <code>cryptography</code> package is installed) or a stdlib AES-256-GCM fallback via
          <code> configure_encryption_key()</code>, and — only if nothing was ever configured — a base64
          placeholder that provides <strong>no confidentiality</strong> and emits a loud <code>UserWarning</code>
          every time it's used.
        </p>
        <div className={`rounded-lg border p-4 text-sm ${t('border-amber-500/20 bg-amber-500/5 text-amber-300', 'border-amber-300 bg-amber-50 text-amber-800')}`}>
          <strong>Configure before storing secrets:</strong> call <code>configure_encryption_key()</code> or
          <code> configure_encryption()</code> before any real secret is ever saved. If you see the base64
          <code>UserWarning</code> in your logs, nothing is actually encrypted yet.
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/fields/numeric" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Numeric Fields
        </Link>
        <Link to="/docs/models/fields/datetime" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Date & Time Fields <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
