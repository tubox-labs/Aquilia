import { useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Command, Loader2, Search, Sparkles } from 'lucide-react'
import { createPortal } from 'react-dom'
import { useTheme } from '../context/ThemeContext'
import { CodeBlock } from './CodeBlock'

interface SearchDocument {
  title: string
  path: string
  aliases: string[]
  section: string
  content: string
  searchableText: string
  codeSamples: SearchCodeSample[]
}

interface SearchCodeSample {
  code: string
  language: string
  filename: string
  searchableText: string
}

interface SearchResultBase {
  id: string
  type: 'page' | 'code'
  title: string
  path: string
  aliases: string[]
  section: string
  score: number
}

interface PageSearchResult extends SearchResultBase {
  type: 'page'
  snippet: string
}

interface CodeSearchResult extends SearchResultBase {
  type: 'code'
  snippet: string
  code: string
  language: string
  filename: string
}

type SearchResult = PageSearchResult | CodeSearchResult

type SearchMode = 'all' | 'pages' | 'code'

interface SearchModeOption {
  key: SearchMode
  label: string
}

const searchModeOptions: SearchModeOption[] = [
  { key: 'all', label: 'All Results' },
  { key: 'pages', label: 'Pages' },
  { key: 'code', label: 'Code' },
]

interface SearchDocumentWithScore extends SearchDocument {
  score: number
  snippet: string
}

interface RouteBinding {
  path: string
  component: string
}

interface ComponentBinding {
  sourcePath: string
  paths: string[]
}

const docsSourceModules = import.meta.glob('../pages/docs/**/*.tsx', {
  query: '?raw',
  import: 'default',
}) as Record<string, () => Promise<string>>

const projectSourceModules = import.meta.glob(['../pages/Changelogs.tsx', '../pages/Releases.tsx'], {
  query: '?raw',
  import: 'default',
}) as Record<string, () => Promise<string>>

const appSourceModules = import.meta.glob('../App.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

const appSource = appSourceModules['../App.tsx'] ?? ''

const extraProjectPages = [
  { path: '/changelogs', sourcePath: '../pages/Changelogs.tsx', title: 'Changelogs', section: 'Project', aliases: ['/docs/changelogs'] },
  { path: '/releases', sourcePath: '../pages/Releases.tsx', title: 'Releases', section: 'Project', aliases: ['/docs/releases'] },
] as const

let cachedSearchIndex: SearchDocument[] | null = null

function toTitleCase(slug: string): string {
  return slug
    .replace(/[-_/]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim()
}

function chooseCanonicalPath(paths: string[]): string {
  return [...paths].sort((left, right) => {
    const leftScore = left.includes('/overview') ? 2 : 0
    const rightScore = right.includes('/overview') ? 2 : 0
    const leftDepth = left.split('/').length
    const rightDepth = right.split('/').length

    if (leftDepth !== rightDepth) return leftDepth - rightDepth
    if (leftScore !== rightScore) return leftScore - rightScore
    return left.localeCompare(right)
  })[0]
}

function decodeEntities(text: string): string {
  return text
    .replace(/&gt;/g, '>')
    .replace(/&lt;/g, '<')
    .replace(/&amp;/g, '&')
}

function normalizeCodeLanguage(language: string): string {
  if (!language.trim()) return 'text'
  return language.trim().toLowerCase()
}

function extractCodeBlocks(source: string): SearchCodeSample[] {
  const blocks: SearchCodeSample[] = []
  const pattern = /<CodeBlock\b([^>]*)>\s*\{`([\s\S]*?)`\}\s*<\/CodeBlock>/g

  for (const match of source.matchAll(pattern)) {
    const attrs = match[1] ?? ''
    const code = decodeEntities((match[2] ?? '').replace(/\r\n/g, '\n').trim())
    if (!code) continue

    const languageMatch = attrs.match(/language\s*=\s*"([^"]+)"/)
    const filenameMatch = attrs.match(/filename\s*=\s*"([^"]+)"/)
    const language = normalizeCodeLanguage(languageMatch?.[1] ?? 'text')
    const filename = (filenameMatch?.[1] ?? 'Code Example').trim()

    blocks.push({
      code,
      language,
      filename,
      searchableText: [filename, language, code].join(' ').toLowerCase(),
    })
  }

  return blocks
}

function extractRenderableSource(source: string): string {
  const returnIndex = source.indexOf('return (')
  if (returnIndex === -1) return source

  let renderable = source.slice(returnIndex + 'return ('.length)
  const tailCloseIndex = renderable.lastIndexOf(')')
  if (tailCloseIndex !== -1) {
    renderable = renderable.slice(0, tailCloseIndex)
  }

  return renderable
}

function cleanForSearch(source: string): string {
  const renderableSource = extractRenderableSource(source)

  return decodeEntities(
    renderableSource
      .replace(/import\s+[\s\S]*?from\s+['"][^'"]+['"];?/g, ' ')
      .replace(/\{\/\*[\s\S]*?\*\/\}/g, ' ')
      .replace(/className=\{[^}]*\}/g, ' ')
      .replace(/className="[^"]*"/g, ' ')
      .replace(/<CodeBlock[\s\S]*?<\/CodeBlock>/g, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\b(?:const|let|var|function|return|export|default|import|from|class|extends|interface|type|async|await)\b/gi, ' ')
      .replace(/[{}()[\],.;:]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim(),
  )
}

function extractTitle(source: string, fallback: string): string {
  const h1Match = source.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)
  if (h1Match) {
    const title = decodeEntities(
      h1Match[1]
        .replace(/<[^>]+>/g, ' ')
        .replace(/\{[^}]+\}/g, ' ')
        .replace(/\s+/g, ' ')
        .trim(),
    )
    if (title.length > 2) return title
  }

  return fallback
}

function inferSection(path: string): string {
  const segments = path.split('/').filter(Boolean)
  if (segments.length <= 1) return 'Getting Started'
  if (segments[0] !== 'docs') return 'Project'
  if (segments.length === 2) {
    if (segments[1] === 'authz') return 'Security'
    return toTitleCase(segments[1])
  }
  if (segments[1] === 'http' && segments[2] === 'api') return 'HTTP API'
  if (segments[1] === 'controllers' && segments[2] === 'decorators') return 'Controller Decorators'
  return toTitleCase(segments[1])
}

function extractComponentImports(source: string): Map<string, string> {
  const componentMap = new Map<string, string>()
  const importPattern = /import\s+\{\s*([A-Za-z0-9_]+)\s*}\s+from\s+['"]\.\/pages\/docs\/([^'"]+)['"]/g

  for (const match of source.matchAll(importPattern)) {
    const component = match[1]
    const importPath = `../pages/docs/${match[2]}.tsx`
    componentMap.set(component, importPath)
  }

  return componentMap
}

function extractDocRoutes(source: string): RouteBinding[] {
  const bindings: RouteBinding[] = []
  const pathRoutePattern = /<Route\s+path="([^"]+)"\s+element={<([A-Za-z0-9_]+)\s*\/>}\s*\/>/g
  const indexRoutePattern = /<Route\s+index\s+element={<([A-Za-z0-9_]+)\s*\/>}\s*\/>/g

  for (const match of source.matchAll(pathRoutePattern)) {
    const pathValue = match[1]
    const component = match[2]
    const normalizedPath = pathValue.startsWith('/') ? pathValue : `/docs/${pathValue}`
    bindings.push({ path: normalizedPath, component })
  }

  for (const match of source.matchAll(indexRoutePattern)) {
    bindings.push({ path: '/docs', component: match[1] })
  }

  return bindings.filter((binding) => binding.path.startsWith('/docs'))
}

function extractSnippet(content: string, query: string): string {
  if (!content) return ''
  const normalizedContent = content.toLowerCase()
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean)
  const firstFound = terms.find((term) => normalizedContent.includes(term))

  if (!firstFound) {
    return content.slice(0, 180).trim()
  }

  const index = normalizedContent.indexOf(firstFound)
  const start = Math.max(0, index - 80)
  const end = Math.min(content.length, index + 120)
  const prefix = start > 0 ? '...' : ''
  const suffix = end < content.length ? '...' : ''
  return `${prefix}${content.slice(start, end).trim()}${suffix}`
}

function extractCodePreview(code: string, query: string): string {
  const lines = code.split('\n')
  if (!lines.length) return ''

  if (!query.trim()) {
    const preview = lines.slice(0, 8).join('\n').trim()
    return lines.length > 8 ? `${preview}\n...` : preview
  }

  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean)
  const firstMatchLine = lines.findIndex((line) => terms.some((term) => line.toLowerCase().includes(term)))

  if (firstMatchLine === -1) {
    const preview = lines.slice(0, 8).join('\n').trim()
    return lines.length > 8 ? `${preview}\n...` : preview
  }

  const start = Math.max(0, firstMatchLine - 2)
  const end = Math.min(lines.length, start + 8)
  const prefix = start > 0 ? '...\n' : ''
  const suffix = end < lines.length ? '\n...' : ''
  return `${prefix}${lines.slice(start, end).join('\n').trim()}${suffix}`
}

function scoreDocument(document: SearchDocument, query: string): number {
  const normalizedQuery = query.trim().toLowerCase()
  if (!normalizedQuery) return 0

  const terms = normalizedQuery.split(/\s+/).filter(Boolean)
  if (!terms.length) return 0

  let score = 0
  const title = document.title.toLowerCase()
  const path = document.path.toLowerCase()
  const section = document.section.toLowerCase()
  const aliases = document.aliases.join(' ').toLowerCase()
  const searchable = document.searchableText

  if (title.includes(normalizedQuery)) score += 220
  if (path.includes(normalizedQuery)) score += 170
  if (aliases.includes(normalizedQuery)) score += 120
  if (searchable.includes(normalizedQuery)) score += 80

  for (const term of terms) {
    if (title.includes(term)) score += 60
    if (section.includes(term)) score += 35
    if (path.includes(term)) score += 45
    if (aliases.includes(term)) score += 28
    if (searchable.includes(term)) score += 14
  }

  const allTermsMatch = terms.every((term) => searchable.includes(term) || title.includes(term) || path.includes(term))
  if (allTermsMatch) score += 55

  if (document.path === '/docs') score += normalizedQuery === 'intro' || normalizedQuery === 'introduction' ? 40 : 0
  score += Math.max(0, 16 - document.path.split('/').length)

  return score
}

function scoreCodeSample(document: SearchDocument, sample: SearchCodeSample, query: string): number {
  const normalizedQuery = query.trim().toLowerCase()
  if (!normalizedQuery) return 0

  const terms = normalizedQuery.split(/\s+/).filter(Boolean)
  if (!terms.length) return 0

  let score = 0
  const filename = sample.filename.toLowerCase()
  const language = sample.language.toLowerCase()
  const code = sample.searchableText
  const title = document.title.toLowerCase()
  const path = document.path.toLowerCase()

  if (filename.includes(normalizedQuery)) score += 220
  if (code.includes(normalizedQuery)) score += 180
  if (language.includes(normalizedQuery)) score += 80
  if (title.includes(normalizedQuery)) score += 70
  if (path.includes(normalizedQuery)) score += 65

  for (const term of terms) {
    if (filename.includes(term)) score += 55
    if (language.includes(term)) score += 25
    if (title.includes(term)) score += 20
    if (path.includes(term)) score += 20
    if (code.includes(term)) score += 14
  }

  const allTermsMatch = terms.every((term) => filename.includes(term) || code.includes(term) || title.includes(term) || path.includes(term))
  if (allTermsMatch) score += 60

  return score
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlightMatch(text: string, query: string, isDark: boolean) {
  const trimmed = query.trim()
  if (!trimmed) return text

  const pattern = new RegExp(`(${escapeRegExp(trimmed)})`, 'ig')
  const parts = text.split(pattern)

  return parts.map((part, index) => {
    const matched = index % 2 === 1
    if (!matched) return <span key={`${part}-${index}`}>{part}</span>
    return (
      <span
        key={`${part}-${index}`}
        className={isDark ? 'bg-aquilia-500/30 text-aquilia-200 rounded px-0.5' : 'bg-aquilia-100 text-aquilia-800 rounded px-0.5'}
      >
        {part}
      </span>
    )
  })
}

async function buildSearchIndex(): Promise<SearchDocument[]> {
  if (!appSource) return []

  const componentMap = extractComponentImports(appSource)
  const routes = extractDocRoutes(appSource)

  const grouped = new Map<string, ComponentBinding>()

  for (const route of routes) {
    const sourcePath = componentMap.get(route.component)
    if (!sourcePath) continue

    const existing = grouped.get(route.component)
    if (existing) {
      existing.paths.push(route.path)
      continue
    }

    grouped.set(route.component, { sourcePath, paths: [route.path] })
  }

  const documents = await Promise.all(
    [...grouped.values()].map(async (binding) => {
      const loadSource = docsSourceModules[binding.sourcePath]
      if (!loadSource) return null

      const source = await loadSource()
      const canonicalPath = chooseCanonicalPath(binding.paths)
      const fallbackTitle = toTitleCase(canonicalPath.replace('/docs/', '').replace('/', ' '))
      const title = extractTitle(source, fallbackTitle)
      const content = cleanForSearch(source)
      const codeSamples = extractCodeBlocks(source)

      return {
        title,
        path: canonicalPath,
        aliases: binding.paths.filter((path) => path !== canonicalPath),
        section: inferSection(canonicalPath),
        content,
        searchableText: [title, canonicalPath, binding.paths.join(' '), content].join(' ').toLowerCase(),
        codeSamples,
      } satisfies SearchDocument
    }),
  )

  const projectDocuments = await Promise.all(
    extraProjectPages.map(async (page) => {
      const loadSource = projectSourceModules[page.sourcePath]
      if (!loadSource) return null

      const source = await loadSource()
      const content = cleanForSearch(source)
      const codeSamples = extractCodeBlocks(source)

      return {
        title: page.title,
        path: page.path,
        aliases: [...page.aliases],
        section: page.section,
        content,
        searchableText: [page.title, page.path, page.aliases.join(' '), content].join(' ').toLowerCase(),
        codeSamples,
      } satisfies SearchDocument
    }),
  )

  return [...documents, ...projectDocuments]
    .filter((document): document is SearchDocument => document !== null)
    .sort((left, right) => left.section.localeCompare(right.section) || left.title.localeCompare(right.title))
}

export function UniversalSearch() {
  const navigate = useNavigate()
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexError, setIndexError] = useState<string | null>(null)
  const [resultMode, setResultMode] = useState<SearchMode>('all')
  const [documents, setDocuments] = useState<SearchDocument[]>(cachedSearchIndex ?? [])
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const commandPressed = event.key.toLowerCase() === 'k' && (event.metaKey || event.ctrlKey)
      if (commandPressed) {
        event.preventDefault()
        setIsOpen((open) => !open)
      }

      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    if (!isOpen) return

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    const timer = window.setTimeout(() => {
      inputRef.current?.focus()
    }, 10)

    return () => {
      document.body.style.overflow = previousOverflow
      window.clearTimeout(timer)
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return
    if (cachedSearchIndex) {
      setDocuments(cachedSearchIndex)
      return
    }

    let active = true
    setIsIndexing(true)
    setIndexError(null)

    void buildSearchIndex()
      .then((index) => {
        if (!active) return
        cachedSearchIndex = index
        setDocuments(index)
      })
      .catch(() => {
        if (!active) return
        setIndexError('Failed to build the documentation search index.')
      })
      .finally(() => {
        if (!active) return
        setIsIndexing(false)
      })

    return () => {
      active = false
    }
  }, [isOpen])

  useEffect(() => {
    setActiveIndex(0)
  }, [query, resultMode])

  const codeExampleCount = useMemo(() => {
    return documents.reduce((total, document) => total + document.codeSamples.length, 0)
  }, [documents])

  const results = useMemo<SearchResult[]>(() => {
    if (!documents.length) return []

    const trimmed = query.trim()

    const pageResultsWithoutQuery: PageSearchResult[] = documents.map((document) => ({
      id: `page:${document.path}`,
      type: 'page',
      title: document.title,
      path: document.path,
      aliases: document.aliases,
      section: document.section,
      score: 0,
      snippet: document.content.slice(0, 170),
    }))

    const codeResultsWithoutQuery: CodeSearchResult[] = documents.flatMap((document) =>
      document.codeSamples.map((sample, index) => ({
        id: `code:${document.path}:${index}`,
        type: 'code',
        title: sample.filename,
        path: document.path,
        aliases: document.aliases,
        section: document.section,
        score: 0,
        snippet: extractSnippet(sample.code.replace(/\s+/g, ' '), ''),
        code: extractCodePreview(sample.code, ''),
        language: sample.language,
        filename: sample.filename,
      })),
    )

    if (!trimmed) {
      if (resultMode === 'pages') {
        return pageResultsWithoutQuery.slice(0, 18)
      }

      if (resultMode === 'code') {
        return codeResultsWithoutQuery.slice(0, 18)
      }

      return [...pageResultsWithoutQuery.slice(0, 10), ...codeResultsWithoutQuery.slice(0, 8)].slice(0, 18)
    }

    const scoredPageResults: PageSearchResult[] = documents
      .map((document): SearchDocumentWithScore => ({
        ...document,
        score: scoreDocument(document, trimmed),
        snippet: extractSnippet(document.content, trimmed),
      }))
      .filter((document) => document.score > 0)
      .sort((left, right) => right.score - left.score)
      .map((document) => ({
        id: `page:${document.path}`,
        type: 'page',
        title: document.title,
        path: document.path,
        aliases: document.aliases,
        section: document.section,
        score: document.score,
        snippet: document.snippet,
      }))

    const scoredCodeResults: CodeSearchResult[] = documents
      .flatMap((document) =>
        document.codeSamples.map((sample, index) => ({
          id: `code:${document.path}:${index}`,
          type: 'code' as const,
          title: sample.filename,
          path: document.path,
          aliases: document.aliases,
          section: document.section,
          score: scoreCodeSample(document, sample, trimmed),
          snippet: extractSnippet(sample.code.replace(/\s+/g, ' '), trimmed),
          code: extractCodePreview(sample.code, trimmed),
          language: sample.language,
          filename: sample.filename,
        })),
      )
      .filter((result) => result.score > 0)
      .sort((left, right) => right.score - left.score)

    if (resultMode === 'pages') {
      return scoredPageResults.slice(0, 18)
    }

    if (resultMode === 'code') {
      return scoredCodeResults.slice(0, 18)
    }

    return [...scoredPageResults, ...scoredCodeResults]
      .sort((left, right) => right.score - left.score)
      .slice(0, 18)
  }, [documents, query, resultMode])

  const openSearch = () => {
    setIsOpen(true)
    setQuery('')
    setActiveIndex(0)
  }

  const goToResult = (result: SearchResult) => {
    setIsOpen(false)
    setQuery('')
    setActiveIndex(0)
    navigate(result.path)
  }

  const onInputKeyDown = (event: ReactKeyboardEvent<HTMLInputElement>) => {
    if (!results.length) return

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((index) => (index + 1) % results.length)
      return
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => (index - 1 + results.length) % results.length)
      return
    }

    if (event.key === 'Enter') {
      event.preventDefault()
      goToResult(results[activeIndex])
    }
  }

  const searchModal = isOpen ? (
    <div className="fixed inset-0 z-[120] flex items-start justify-center px-4 pt-24 lg:pt-28" role="dialog" aria-modal="true">
      <button
        type="button"
        aria-label="Close search"
        className="absolute inset-0 bg-black/70 backdrop-blur-md"
        onClick={() => setIsOpen(false)}
      />

      <div
        className={`relative w-[min(96vw,78rem)] rounded-3xl border shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 ${isDark ? 'bg-[#070709]/95 border-white/15' : 'bg-white/95 border-gray-200'}`}
        style={{ boxShadow: isDark ? '0 30px 80px rgba(10, 116, 255, 0.22)' : '0 30px 80px rgba(15, 23, 42, 0.12)' }}
      >
        <div className="pointer-events-none absolute -top-20 -right-20 h-56 w-56 rounded-full bg-aquilia-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 -left-20 h-56 w-56 rounded-full bg-sky-500/20 blur-3xl" />

        <div className="relative p-5 sm:p-6">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-aquilia-500" />
              <span className={`text-xs uppercase tracking-[0.18em] font-semibold ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                Aquilia Documentation Search
              </span>
            </div>
            <div className={`hidden sm:flex items-center gap-1 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <span className={`px-2 py-0.5 rounded border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>Esc</span>
              Close
            </div>
          </div>

          <div className={`relative flex items-center rounded-2xl border px-4 py-3 ${isDark ? 'bg-black/40 border-white/10' : 'bg-gray-50/90 border-gray-200'}`}>
            <Search className={`w-5 h-5 mr-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
            <input
              ref={inputRef}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={onInputKeyDown}
              placeholder="Search documentation, API reference, guides, tutorials, releases, and changelogs..."
              className={`w-full bg-transparent outline-none text-base ${isDark ? 'text-white placeholder:text-gray-500' : 'text-gray-900 placeholder:text-gray-400'}`}
            />
            <div className={`hidden sm:flex items-center gap-1 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <span className={`px-2 py-0.5 rounded border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>↑↓</span>
              <span className={`px-2 py-0.5 rounded border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>Enter</span>
            </div>
          </div>

          <div className={`mt-3 mb-4 text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'} flex items-center justify-between`}>
            <span>{isIndexing ? 'Building documentation search index...' : `Indexed ${documents.length} pages and ${codeExampleCount} code examples`}</span>
            <span>Scope: documentation, API reference, guides, code, releases, changelogs</span>
          </div>

          <div className="flex items-center gap-2 mb-3">
            {searchModeOptions.map((option) => {
              const isActive = resultMode === option.key
              return (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setResultMode(option.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${isActive
                    ? isDark
                      ? 'bg-aquilia-500/20 border-aquilia-500/40 text-aquilia-200'
                      : 'bg-aquilia-50 border-aquilia-300 text-aquilia-700'
                    : isDark
                      ? 'border-white/10 text-gray-400 hover:text-white hover:bg-white/5'
                      : 'border-gray-200 text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                >
                  {option.label}
                </button>
              )
            })}
          </div>

          <div className="max-h-[58vh] overflow-y-auto mt-1">
            {isIndexing && (
              <div className={`px-4 py-8 flex items-center justify-center gap-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Indexing every documentation module...</span>
              </div>
            )}

            {!isIndexing && indexError && (
              <div className={`px-4 py-8 text-sm text-center ${isDark ? 'text-rose-300' : 'text-rose-600'}`}>
                {indexError}
              </div>
            )}

            {!isIndexing && !indexError && results.length === 0 && (
              <div className={`px-4 py-8 text-sm text-center ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                No matches found in this mode. Try broader terms like "session", "fault", "middleware", or switch between Pages and Code.
              </div>
            )}

            {!isIndexing && !indexError && results.map((result, index) => {
              const isActive = index === activeIndex

              if (result.type === 'code') {
                return (
                  <div
                    key={result.id}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={`border-b last:border-b-0 transition-all duration-150 ${isDark ? 'border-white/5' : 'border-gray-100'} ${isActive
                      ? isDark
                        ? 'bg-aquilia-500/12'
                        : 'bg-aquilia-50'
                      : isDark
                        ? 'hover:bg-white/5'
                        : 'hover:bg-gray-50'
                      }`}
                  >
                    <button
                      type="button"
                      onClick={() => goToResult(result)}
                      className="w-full text-left px-4 sm:px-5 py-4"
                    >
                      <div className="flex items-start gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                              {highlightMatch(result.title, query, isDark)}
                            </span>
                            <span className={`text-[11px] uppercase tracking-wider px-2 py-0.5 rounded-full ${isDark ? 'bg-aquilia-500/20 text-aquilia-200' : 'bg-aquilia-100 text-aquilia-700'}`}>
                              Code Example
                            </span>
                            <span className={`text-[11px] uppercase tracking-wider px-2 py-0.5 rounded-full ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-100 text-gray-500'}`}>
                              {result.section}
                            </span>
                          </div>
                          <p className={`text-xs mt-1 ${isDark ? 'text-aquilia-300' : 'text-aquilia-700'}`}>{result.path}</p>
                          <p className={`text-sm mt-2 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{highlightMatch(result.snippet, query, isDark)}</p>
                          {result.aliases.length > 0 && (
                            <p className={`text-xs mt-2 truncate ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                              Aliases: {result.aliases.join(', ')}
                            </p>
                          )}
                        </div>
                        <ArrowRight className={`w-4 h-4 mt-1 transition-transform ${isActive ? 'translate-x-0.5 text-aquilia-500' : isDark ? 'text-gray-600' : 'text-gray-400'}`} />
                      </div>
                    </button>

                    <div className="px-4 sm:px-5 pb-4" onClick={(event) => event.stopPropagation()}>
                      <CodeBlock
                        code={result.code}
                        language={result.language}
                        filename={result.filename}
                        showLineNumbers={false}
                        compact
                      />
                    </div>
                  </div>
                )
              }

              return (
                <button
                  key={result.id}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => goToResult(result)}
                  className={`w-full text-left px-4 sm:px-5 py-4 border-b last:border-b-0 transition-all duration-150 ${isDark ? 'border-white/5' : 'border-gray-100'} ${isActive
                    ? isDark
                      ? 'bg-aquilia-500/12'
                      : 'bg-aquilia-50'
                    : isDark
                      ? 'hover:bg-white/5'
                      : 'hover:bg-gray-50'
                    }`}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                          {highlightMatch(result.title, query, isDark)}
                        </span>
                        <span className={`text-[11px] uppercase tracking-wider px-2 py-0.5 rounded-full ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-100 text-gray-500'}`}>
                          {result.section}
                        </span>
                      </div>
                      <p className={`text-xs mt-1 ${isDark ? 'text-aquilia-300' : 'text-aquilia-700'}`}>{result.path}</p>
                      <p className={`text-sm mt-2 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{highlightMatch(result.snippet, query, isDark)}</p>
                      {result.aliases.length > 0 && (
                        <p className={`text-xs mt-2 truncate ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                          Aliases: {result.aliases.join(', ')}
                        </p>
                      )}
                    </div>
                    <ArrowRight className={`w-4 h-4 mt-1 transition-transform ${isActive ? 'translate-x-0.5 text-aquilia-500' : isDark ? 'text-gray-600' : 'text-gray-400'}`} />
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  ) : null

  return (
    <>
      <button
        onClick={openSearch}
        className={`hidden md:flex relative overflow-hidden items-center gap-3 rounded-xl border px-4 h-10 min-w-[14rem] xl:min-w-[18rem] transition-all duration-300 group ${isDark
          ? 'bg-[#0b0b0f]/70 border-white/10 text-gray-400 hover:border-aquilia-500/40 hover:bg-[#101018]'
          : 'bg-white/90 border-gray-200 text-gray-500 hover:border-aquilia-300 hover:bg-white'
          }`}
        title="Search Aquilia (Cmd/Ctrl + K)"
      >
        <Search className="w-4 h-4" />
        <span className="text-sm text-left">Search Aquilia...</span>
        <span className={`ml-auto inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium border ${isDark ? 'border-white/10 text-gray-500' : 'border-gray-200 text-gray-400'}`}>
          <Command className="w-3 h-3" />K
        </span>
        <div className={`absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r ${isDark ? 'from-transparent via-white/5 to-transparent' : 'from-transparent via-gray-200 to-transparent'}`} />
      </button>

      <button
        onClick={openSearch}
        className={`md:hidden p-2 rounded-lg transition-all duration-200 relative overflow-hidden group ${isDark ? 'hover:bg-white/10 text-gray-400 hover:text-white' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-900'}`}
        title="Search Aquilia"
      >
        <Search className="w-5 h-5" />
      </button>

      {searchModal && typeof document !== 'undefined' ? createPortal(searchModal, document.body) : null}
    </>
  )
}
