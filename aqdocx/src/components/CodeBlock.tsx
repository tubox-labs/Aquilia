import { useState, useCallback } from 'react'
import { Copy, Check, Braces, Settings, FileCode } from 'lucide-react'
import { Highlight } from 'prism-react-renderer'
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
import { aquiliaDarkTheme, aquiliaLightTheme } from '../lib/prismThemes'

if (!Prism.languages.plain) {
  const plainGrammar = {}
  Prism.languages.plain = plainGrammar
  Prism.languages.plaintext = plainGrammar
  Prism.languages.text = plainGrammar
  Prism.languages.txt = plainGrammar
}

interface CodeBlockProps {
  code?: string
  children?: string
  language?: string
  filename?: string
  title?: string
  showLineNumbers?: boolean
  compact?: boolean
  highlightLines?: number[]
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

function getLanguageIcon(language: string) {
  const norm = language.toLowerCase().trim()

  // Map language to Devicon slug
  const deviconMap: Record<string, string> = {
    python: 'python/python-original.svg',
    py: 'python/python-original.svg',
    typescript: 'typescript/typescript-original.svg',
    ts: 'typescript/typescript-original.svg',
    tsx: 'typescript/typescript-original.svg',
    javascript: 'javascript/javascript-original.svg',
    js: 'javascript/javascript-original.svg',
    jsx: 'javascript/javascript-original.svg',
    bash: 'bash/bash-original.svg',
    sh: 'bash/bash-original.svg',
    zsh: 'bash/bash-original.svg',
    shell: 'bash/bash-original.svg',
    terminal: 'bash/bash-original.svg',
    console: 'bash/bash-original.svg',
    docker: 'docker/docker-original.svg',
    dockerfile: 'docker/docker-original.svg',
    yaml: 'yaml/yaml-original.svg',
    yml: 'yaml/yaml-original.svg',
    markdown: 'markdown/markdown-original.svg',
    md: 'markdown/markdown-original.svg',
  }

  const deviconSlug = deviconMap[norm]
  if (deviconSlug) {
    return (
      <img
        src={`https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/${deviconSlug}`}
        className="w-4.5 h-4.5 object-contain grayscale brightness-0 dark:invert opacity-50"
        alt={language}
        loading="lazy"
      />
    )
  }

  // Fallback to Lucide icons
  if (['json'].includes(norm)) {
    return <Braces className="w-4.5 h-4.5 text-gray-500 dark:text-gray-400 shrink-0" />
  }

  if (['toml', 'ini', 'conf'].includes(norm)) {
    return <Settings className="w-4.5 h-4.5 text-gray-500 dark:text-gray-400 shrink-0" />
  }

  return <FileCode className="w-4.5 h-4.5 text-gray-500 dark:text-gray-400 shrink-0" />
}

export function CodeBlock({ code, children, language = 'python', filename, title, showLineNumbers = true, compact = false, highlightLines = [] }: CodeBlockProps) {
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

  const classReferenceColor = isDark ? '#fa993f' : '#c2410c'
  const decoratorColor = isDark ? '#22c55e' : '#15803d'
  const variableColor = isDark ? '#93c5fd' : '#1d4ed8'
  const memberColor = isDark ? '#67e8f9' : '#0e7490'
  const functionCallColor = isDark ? '#fde047' : '#a16207'
  const selfColor = isDark ? '#f472b6' : '#be185d'
  const canApplyClassFallback = CLASS_FALLBACK_LANGUAGES.has(prismLanguage)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(codeContent)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [codeContent])

  return (
    <div className={`group relative code-block-container ${compact ? 'my-2' : 'my-6'}`}>
      <div className="absolute -inset-0.5 bg-gradient-to-r from-aquilia-500/10 to-blue-500/10 rounded-xl blur opacity-0 group-hover:opacity-100 transition print:hidden" />
      <div className={`relative rounded-xl overflow-hidden border ${isDark ? 'bg-black border-white/10' : 'bg-[#f8fafc] border-gray-200'}`}>
        {/* Header with language icon */}
        <div className={`flex items-center justify-between ${compact ? 'px-3 py-2' : 'px-4 py-2.5'} border-b ${isDark ? 'border-white/5 bg-white/[0.02]' : 'border-gray-200 bg-gray-50/80'}`}>
          <div className="flex items-center gap-3">
            {getLanguageIcon(normalizedLanguage)}
            <div className="flex items-center gap-2">
              <span className={`font-mono uppercase tracking-wider ${compact ? 'text-[10px]' : 'text-xs'} ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                {title || filename || language}
              </span>
            </div>
          </div>
          <button
            onClick={handleCopy}
            className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-all print:hidden ${copied
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
            <pre className={`${compact ? 'py-3 text-xs' : 'py-4 text-sm'} overflow-x-auto leading-relaxed font-mono ${isDark ? 'bg-black' : 'bg-[#f8fafc]'}`}>
              {tokens.map((line, i) => {
                const lineProps = getLineProps({ line })
                const isHighlighted = highlightLines.includes(i + 1)
                return (
                  <div
                    key={i}
                    {...lineProps}
                    className={`${lineProps.className || ''} ${compact ? 'px-3' : 'px-4'} ${
                      isHighlighted
                        ? isDark
                          ? 'bg-aquilia-500/15 border-l-2 border-aquilia-500'
                          : 'bg-aquilia-500/5 border-l-2 border-aquilia-500'
                        : 'border-l-2 border-transparent'
                    }`}
                  >
                  {showLineNumbers && (
                    <span className={`inline-block ${compact ? 'w-6 mr-3' : 'w-8 mr-4'} text-right select-none ${isDark ? 'text-gray-700' : 'text-gray-300'}`}>
                      {i + 1}
                    </span>
                  )}
                  {line.map((token, key) => {
                    const tokenProps = getTokenProps({ token })

                    if (token.types.includes('decorator') || token.types.includes('annotation')) {
                      return (
                        <span key={key} className={`${tokenProps.className} code-decorator`} style={{ ...tokenProps.style, color: decoratorColor }}>
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
                          let tokenClassName = 'code-variable'
                          if (SELF_IDENTIFIERS.has(segment)) {
                            color = selfColor
                            tokenClassName = 'code-self'
                          } else if (isClassReference) {
                            color = classReferenceColor
                            tokenClassName = 'code-class-ref'
                          } else if (nextChar === '(') {
                            color = functionCallColor
                            tokenClassName = 'code-function-call'
                          } else if (prevChar === '.') {
                            color = memberColor
                            tokenClassName = 'code-member'
                          }

                          return <span key={segmentIndex} className={tokenClassName} style={{ color }}>{segment}</span>
                        })}
                      </span>
                    )
                  })}
                </div>
              )})}
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
