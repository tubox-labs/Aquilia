import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function Savepoints() {
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
        <span className={t('text-gray-300','text-gray-600')}>Savepoints & Nesting</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Savepoints & Nesting</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Nesting transaction blocks automatically maps to SQL <code>SAVEPOINT</code> statements, allowing selective inner rollbacks.
        </p>
      </div>

      {/* Nested transactions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Nesting and Isolation</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          The outermost <code>atomic()</code> block initiates a transaction. Nested <code>atomic()</code> blocks create savepoints. Exceptions in nested blocks must be caught to prevent rolling back the parent block:
        </p>
        <CodeBlock language="python">{`async with atomic() as sp1:
    await User.create(name="Bob")
    
    try:
        async with atomic() as sp2:
            await Post.create(title="Hello")
            raise ValueError("nested exception")  # sp2 rolls back here
    except ValueError:
        pass  # Exception is caught; sp1 remains active and uncompromised

    # Bob will be saved, Post will be rolled back`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/transactions/atomic" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Atomic & Contexts
        </Link>
        <Link to="/docs/models/transactions/hooks" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Lifecycle Hooks <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
