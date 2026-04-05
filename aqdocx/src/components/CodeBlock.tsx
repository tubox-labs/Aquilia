import { useState, useCallback } from 'react'
import { Copy, Check, Terminal } from 'lucide-react'
import { Highlight, type PrismTheme } from 'prism-react-renderer'
import Prism from 'prismjs'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-jsx'
import 'prismjs/components/prism-tsx'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-shell-session'
import 'prismjs/components/prism-yaml'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-markdown'
import 'prismjs/components/prism-ini'
import 'prismjs/components/prism-toml'
import 'prismjs/components/prism-docker'
import { useTheme } from '../context/ThemeContext'

if (!Prism.languages.plain) {
  const plainGrammar = {}
  Prism.languages.plain = plainGrammar
  Prism.languages.plaintext = plainGrammar
  Prism.languages.text = plainGrammar
  Prism.languages.txt = plainGrammar
}

/*
 * Custom Aquilia syntax highlighting — mirrors the temp/docs/ palette:
 *   Keywords / builtins   → aquilia green (#22c55e)
 *   Strings               → green-400 (#4ade80)
 *   Numbers / booleans    → blue-400 (#60a5fa)
 *   Functions             → yellow-300 (#fde047)
 *   Comments              → gray-500 (#6b7280)
 *   Decorators / imports  → aquilia green (#22c55e)
 *   Class names           → orange-400 (#fb923c)
 *   Plain text            → gray-200 (#e5e7eb)
 */
const aquiliaDarkTheme: PrismTheme = {
  plain: { color: '#e5e7eb', backgroundColor: '#000000' },
  styles: [
    { types: ['comment', 'prolog', 'doctype', 'cdata'], style: { color: '#6b7280', fontStyle: 'italic' as const } },
    { types: ['keyword', 'builtin', 'tag', 'selector', 'important'], style: { color: '#22c55e' } },
    { types: ['string', 'char', 'attr-value', 'template-string', 'template-punctuation'], style: { color: '#4ade80' } },
    { types: ['number', 'boolean', 'constant'], style: { color: '#60a5fa' } },
    { types: ['function', 'function-variable'], style: { color: '#fde047' } },
    { types: ['class-name', 'maybe-class-name'], style: { color: '#fb923c' } },
    { types: ['decorator', 'annotation', 'atrule'], style: { color: '#22c55e' } },
    { types: ['operator', 'punctuation'], style: { color: '#d1d5db' } },
    { types: ['variable', 'parameter'], style: { color: '#e5e7eb' } },
    { types: ['property', 'attr-name'], style: { color: '#93c5fd' } },
    { types: ['assign-left', 'key', 'section', 'section-name', 'table'], style: { color: '#93c5fd' } },
    { types: ['value'], style: { color: '#4ade80' } },
    { types: ['command', 'instruction'], style: { color: '#fde047' } },
    { types: ['shell-symbol'], style: { color: '#22c55e' } },
    { types: ['output'], style: { color: '#9ca3af' } },
    { types: ['regex'], style: { color: '#fbbf24' } },
    { types: ['deleted'], style: { color: '#ef4444' } },
    { types: ['inserted'], style: { color: '#22c55e' } },
    { types: ['namespace'], style: { color: '#fb923c', opacity: 0.8 } },
    { types: ['symbol'], style: { color: '#a78bfa' } },
    { types: ['entity', 'url'], style: { color: '#60a5fa' } },
    { types: ['plain'], style: { color: '#e5e7eb' } },
  ],
}

const aquiliaLightTheme: PrismTheme = {
  plain: { color: '#1e293b', backgroundColor: '#f8fafc' },
  styles: [
    { types: ['comment', 'prolog', 'doctype', 'cdata'], style: { color: '#94a3b8', fontStyle: 'italic' as const } },
    { types: ['keyword', 'builtin', 'tag', 'selector', 'important'], style: { color: '#15803d' } },
    { types: ['string', 'char', 'attr-value', 'template-string', 'template-punctuation'], style: { color: '#16a34a' } },
    { types: ['number', 'boolean', 'constant'], style: { color: '#2563eb' } },
    { types: ['function', 'function-variable'], style: { color: '#a16207' } },
    { types: ['class-name', 'maybe-class-name'], style: { color: '#c2410c' } },
    { types: ['decorator', 'annotation', 'atrule'], style: { color: '#15803d' } },
    { types: ['operator', 'punctuation'], style: { color: '#475569' } },
    { types: ['variable', 'parameter'], style: { color: '#1e293b' } },
    { types: ['property', 'attr-name'], style: { color: '#2563eb' } },
    { types: ['assign-left', 'key', 'section', 'section-name', 'table'], style: { color: '#1d4ed8' } },
    { types: ['value'], style: { color: '#16a34a' } },
    { types: ['command', 'instruction'], style: { color: '#a16207' } },
    { types: ['shell-symbol'], style: { color: '#15803d' } },
    { types: ['output'], style: { color: '#64748b' } },
    { types: ['regex'], style: { color: '#d97706' } },
    { types: ['deleted'], style: { color: '#dc2626' } },
    { types: ['inserted'], style: { color: '#16a34a' } },
    { types: ['namespace'], style: { color: '#c2410c', opacity: 0.8 } },
    { types: ['symbol'], style: { color: '#7c3aed' } },
    { types: ['entity', 'url'], style: { color: '#2563eb' } },
    { types: ['plain'], style: { color: '#1e293b' } },
  ],
}

interface CodeBlockProps {
  code?: string
  children?: string
  language?: string
  filename?: string
  title?: string
  showLineNumbers?: boolean
  compact?: boolean
}

const CLASS_REFERENCE_PATTERN = /^([A-Z][A-Za-z0-9_]*[a-z][A-Za-z0-9_]*)$/
const CLASS_FALLBACK_LANGUAGES = new Set(['python', 'typescript', 'javascript', 'tsx', 'jsx'])
const IDENTIFIER_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/
const SELF_IDENTIFIERS = new Set(['self', 'cls', 'this', 'super'])

function splitIdentifierSegments(content: string): string[] {
  return content.split(/([A-Za-z_][A-Za-z0-9_]*)/g).filter((segment) => segment.length > 0)
}

function getFirstNonWhitespaceChar(content: string): string | null {
  for (const char of content) {
    if (!/\s/.test(char)) {
      return char
    }
  }
  return null
}

function getLastNonWhitespaceChar(content: string): string | null {
  for (let i = content.length - 1; i >= 0; i -= 1) {
    const char = content[i]
    if (!/\s/.test(char)) {
      return char
    }
  }
  return null
}

function getNeighborChars(tokens: Array<{ content: string }>, tokenIndex: number, segments: string[], segmentIndex: number): {
  prevChar: string | null
  nextChar: string | null
} {
  const prevSegment = segments.slice(0, segmentIndex).join('')
  const nextSegment = segments.slice(segmentIndex + 1).join('')

  let prevChar = getLastNonWhitespaceChar(prevSegment)
  let nextChar = getFirstNonWhitespaceChar(nextSegment)

  if (prevChar === null) {
    for (let i = tokenIndex - 1; i >= 0; i -= 1) {
      prevChar = getLastNonWhitespaceChar(tokens[i].content)
      if (prevChar !== null) {
        break
      }
    }
  }

  if (nextChar === null) {
    for (let i = tokenIndex + 1; i < tokens.length; i += 1) {
      nextChar = getFirstNonWhitespaceChar(tokens[i].content)
      if (nextChar !== null) {
        break
      }
    }
  }

  return { prevChar, nextChar }
}

export function CodeBlock({ code, children, language = 'python', filename, title, showLineNumbers = true, compact = false }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const codeContent = (code || children || '').trim()
  const normalizedLanguage = language.trim().toLowerCase()

  // Map language aliases so Prism can highlight everything
  const prismLanguage = (() => {
    const map: Record<string, string> = {
      shell: 'bash',
      sh: 'bash',
      zsh: 'bash',
      terminal: 'bash',
      console: 'bash',
      'shell-session': 'shell-session',
      shellsession: 'shell-session',
      shellscript: 'bash',
      dockerfile: 'docker',
      plaintext: 'plain',
      text: 'plain',
      txt: 'plain',
      structure: 'plain',
      py: 'python',
      js: 'javascript',
      ts: 'typescript',
      yml: 'yaml',
      md: 'markdown',
      conf: 'ini',
    }
    return map[normalizedLanguage] || normalizedLanguage
  })()

  const classReferenceColor = isDark ? '#fb923c' : '#c2410c'
  const decoratorColor = isDark ? '#22c55e' : '#15803d'
  const variableColor = isDark ? '#93c5fd' : '#1d4ed8'
  const memberColor = isDark ? '#67e8f9' : '#0e7490'
  const functionCallColor = isDark ? '#fde047' : '#a16207'
  const selfColor = isDark ? '#f472b6' : '#be185d'
  const canApplyClassFallback = CLASS_FALLBACK_LANGUAGES.has(prismLanguage)

  const isTerminal = ['bash', 'shell', 'sh', 'zsh', 'terminal', 'console', 'shell-session', 'shellsession'].includes(normalizedLanguage)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(codeContent)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [codeContent])

  return (
    <div className={`group relative ${compact ? 'my-2' : 'my-6'}`}>
      <div className="absolute -inset-0.5 bg-gradient-to-r from-aquilia-500/10 to-blue-500/10 rounded-xl blur opacity-0 group-hover:opacity-100 transition" />
      <div className={`relative rounded-xl overflow-hidden border ${isDark ? 'bg-black border-white/10' : 'bg-[#f8fafc] border-gray-200'}`}>
        {/* Header with macOS traffic-light dots */}
        <div className={`flex items-center justify-between ${compact ? 'px-3 py-2' : 'px-4 py-2.5'} border-b ${isDark ? 'border-white/5 bg-white/[0.02]' : 'border-gray-200 bg-gray-50/80'}`}>
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5 opacity-50">
              <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
              <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
              <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
            </div>
            <div className="flex items-center gap-2">
              {isTerminal && <Terminal className="w-3.5 h-3.5 text-aquilia-500" />}
              <span className={`font-mono uppercase tracking-wider ${compact ? 'text-[10px]' : 'text-xs'} ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                {title || filename || language}
              </span>
            </div>
          </div>
          <button
            onClick={handleCopy}
            className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-all ${copied
              ? 'text-aquilia-400 bg-aquilia-500/10'
              : `${isDark ? 'text-gray-500 hover:text-white hover:bg-white/10' : 'text-gray-400 hover:text-gray-700 hover:bg-gray-200'}`
              }`}
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        {/* Code body */}
        <Highlight prism={Prism as any} theme={isDark ? aquiliaDarkTheme : aquiliaLightTheme} code={codeContent} language={prismLanguage as any}>
          {({ tokens, getLineProps, getTokenProps }) => (
            <pre className={`${compact ? 'p-3 text-xs' : 'p-4 text-sm'} overflow-x-auto leading-relaxed font-mono ${isDark ? 'bg-black' : 'bg-[#f8fafc]'}`}>
              {tokens.map((line, i) => (
                <div key={i} {...getLineProps({ line })}>
                  {showLineNumbers && (
                    <span className={`inline-block ${compact ? 'w-6 mr-3' : 'w-8 mr-4'} text-right select-none ${isDark ? 'text-gray-700' : 'text-gray-300'}`}>
                      {i + 1}
                    </span>
                  )}
                  {line.map((token, key) => {
                    const tokenProps = getTokenProps({ token })

                    if (token.types.includes('decorator') || token.types.includes('annotation')) {
                      return (
                        <span key={key} className={tokenProps.className} style={{ ...tokenProps.style, color: decoratorColor }}>
                          {token.content}
                        </span>
                      )
                    }

                    if (!canApplyClassFallback || !token.types.includes('plain') || typeof token.content !== 'string') {
                      return <span key={key} {...tokenProps} />
                    }

                    const segments = splitIdentifierSegments(token.content)
                    const hasIdentifiers = segments.some((segment) => IDENTIFIER_PATTERN.test(segment))

                    if (!hasIdentifiers) {
                      return <span key={key} {...tokenProps} />
                    }

                    return (
                      <span key={key} className={tokenProps.className} style={tokenProps.style}>
                        {segments.map((segment, segmentIndex) => {
                          if (!IDENTIFIER_PATTERN.test(segment)) {
                            return <span key={segmentIndex}>{segment}</span>
                          }

                          const { prevChar, nextChar } = getNeighborChars(line as Array<{ content: string }>, key, segments, segmentIndex)
                          const isClassReference = CLASS_REFERENCE_PATTERN.test(segment)

                          let color = variableColor
                          if (SELF_IDENTIFIERS.has(segment)) {
                            color = selfColor
                          } else if (isClassReference) {
                            color = classReferenceColor
                          } else if (nextChar === '(') {
                            color = functionCallColor
                          } else if (prevChar === '.') {
                            color = memberColor
                          }

                          return <span key={segmentIndex} style={{ color }}>{segment}</span>
                        })}
                      </span>
                    )
                  })}
                </div>
              ))}
            </pre>
          )}
        </Highlight>
      </div>
    </div>
  )
}

/* Simple inline code */
export function InlineCode({ children }: { children: React.ReactNode }) {
  return <code className="text-aquilia-400">{children}</code>
}
