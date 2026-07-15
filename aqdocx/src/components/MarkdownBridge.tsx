import React from 'react'
import { Link } from 'react-router-dom'
import { marked } from 'marked'
import { CodeBlock } from './CodeBlock'
import { DocTerm } from './docPreview/DocTerm'
import { getAllDocEntities } from '../lib/docPreview/registry'
import { useTheme } from '../context/ThemeContext'
import {
  Info,
  Zap,
  AlertTriangle,
  AlertOctagon
} from 'lucide-react'

interface MarkdownBridgeProps {
  content: string
  version: string
  currentPage: string
}

let titleToIdMap: Map<string, string> | null = null

function getTitleToIdMap() {
  if (titleToIdMap) return titleToIdMap
  titleToIdMap = new Map<string, string>()
  const entities = getAllDocEntities()
  entities.forEach(entity => {
    // Exact title match (case insensitive)
    titleToIdMap!.set(entity.title.toLowerCase(), entity.id)
    
    // Clean title match (strip leading @ for decorators, e.g., @authenticated -> authenticated)
    const cleanTitle = entity.title.replace(/^@/, '').toLowerCase()
    titleToIdMap!.set(cleanTitle, entity.id)
    
    // If the title contains spaces or is a method, map variations
    const snakeTitle = cleanTitle.replace(/\s+/g, '_')
    titleToIdMap!.set(snakeTitle, entity.id)

    // Match last part of ID for nested namespaces
    if (entity.id.includes('.')) {
      const parts = entity.id.split('.')
      const lastPart = parts[parts.length - 1]
      if (!titleToIdMap!.has(lastPart)) {
        titleToIdMap!.set(lastPart, entity.id)
      }
    }
  })
  return titleToIdMap
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim()
}

export function MarkdownBridge({ content, version, currentPage }: MarkdownBridgeProps) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const tokens = marked.lexer(content)

  const renderInlineTokens = (inlineTokens: any[]): React.ReactNode[] => {
    if (!inlineTokens) return []
    const map = getTitleToIdMap()
    
    return inlineTokens.map((token, idx) => {
      switch (token.type) {
        case 'text':
        case 'escape':
          return <span key={idx}>{token.tokens ? renderInlineTokens(token.tokens) : token.text}</span>
        case 'codespan': {
          const text = token.text.trim()
          const termId = map.get(text.toLowerCase())
          if (termId) {
            return <DocTerm key={idx} id={termId}>{text}</DocTerm>
          }
          return (
            <code key={idx} className="text-aquilia-500 dark:text-aquilia-400 bg-aquilia-500/5 px-1.5 py-0.5 rounded font-mono text-xs border border-aquilia-500/10">
              {text}
            </code>
          )
        }
        case 'link': {
          const href = token.href || ''
          const isExternal = href.startsWith('http://') || href.startsWith('https://') || href.startsWith('//')
          const isLocalMarkdown = href.endsWith('.md') || href.includes('.md#')
          
          if (isLocalMarkdown) {
            const hashIndex = href.indexOf('#')
            let pagePath = href
            let hash = ''
            if (hashIndex !== -1) {
              pagePath = href.substring(0, hashIndex)
              hash = href.substring(hashIndex)
            }
            const pageName = pagePath.replace(/\.md$/, '')
            const targetPath = pageName === 'README' 
              ? `/releases/${version}${hash}` 
              : `/releases/${version}/${pageName}${hash}`
            return (
              <Link
                key={idx}
                to={targetPath}
                className="text-aquilia-500 hover:text-aquilia-400 transition-colors font-medium underline decoration-aquilia-500/20 hover:decoration-aquilia-500"
              >
                {token.text}
              </Link>
            )
          } else if (href.startsWith('#')) {
            const targetPath = currentPage === 'README'
              ? `/releases/${version}${href}`
              : `/releases/${version}/${currentPage}${href}`
            return (
              <Link
                key={idx}
                to={targetPath}
                className="text-aquilia-500 hover:text-aquilia-400 transition-colors font-medium underline decoration-aquilia-500/20 hover:decoration-aquilia-500"
              >
                {token.text}
              </Link>
            )
          } else {
            return (
              <a
                key={idx}
                href={href}
                target={isExternal ? '_blank' : undefined}
                rel={isExternal ? 'noopener noreferrer' : undefined}
                className="text-aquilia-500 hover:text-aquilia-400 transition-colors font-medium underline decoration-aquilia-500/20 hover:decoration-aquilia-500"
              >
                {token.text}
              </a>
            )
          }
        }
        case 'strong':
          return (
            <strong key={idx} className="font-bold text-gray-900 dark:text-white">
              {renderInlineTokens(token.tokens)}
            </strong>
          )
        case 'em':
          return (
            <em key={idx} className="italic">
              {renderInlineTokens(token.tokens)}
            </em>
          )
        case 'br':
          return <br key={idx} />
        case 'del':
          return (
            <del key={idx} className="line-through opacity-60">
              {token.tokens ? renderInlineTokens(token.tokens) : token.text}
            </del>
          )
        case 'image':
          return (
            <img
              key={idx}
              src={token.href}
              alt={token.text}
              title={token.title || undefined}
              className="max-w-full h-auto rounded-lg my-4 inline-block shadow-sm"
            />
          )
        case 'html':
          return <span key={idx} dangerouslySetInnerHTML={{ __html: token.text }} />
        default:
          return <span key={idx}>{token.text}</span>
      }
    })
  }

  const parseAlert = (token: any) => {
    if (token.type !== 'blockquote' || !token.tokens || token.tokens.length === 0) return null
    const firstChild = token.tokens[0]
    if (firstChild.type !== 'paragraph' || !firstChild.text) return null
    
    const match = firstChild.text.match(/^\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION|INFO)\]/i)
    if (!match) return null
    
    const typeStr = match[1].toUpperCase()
    let kind: 'note' | 'tip' | 'warning' | 'important' = 'note'
    let title = 'Note'
    
    if (typeStr === 'TIP') {
      kind = 'tip'
      title = 'Tip'
    } else if (typeStr === 'WARNING') {
      kind = 'warning'
      title = 'Warning'
    } else if (typeStr === 'IMPORTANT' || typeStr === 'CAUTION') {
      kind = 'important'
      title = 'Important'
    } else {
      kind = 'note'
      title = 'Note'
    }
    
    const cleanTokens = [...token.tokens]
    const firstPara = { ...cleanTokens[0] }
    
    const prefixLength = match[0].length
    firstPara.text = firstPara.text.substring(prefixLength).trim()
    
    if (firstPara.tokens && firstPara.tokens.length > 0) {
      const firstInline = { ...firstPara.tokens[0] }
      if (firstInline.type === 'text') {
        firstInline.text = firstInline.text.replace(/^\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION|INFO)\]/i, '').trim()
        firstPara.tokens = [firstInline, ...firstPara.tokens.slice(1)]
      }
    }
    cleanTokens[0] = firstPara
    
    return { kind, title, cleanTokens }
  }

  const renderBlock = (token: any, blockIdx: number): React.ReactNode => {
    switch (token.type) {
      case 'heading': {
        const text = token.text
        const slug = slugify(text)
        const HeadingTag = `h${token.depth}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
        
        let headingStyle = ''
        if (token.depth === 1) {
          headingStyle = 'text-3.5xl font-extrabold tracking-tight mb-8 mt-4 font-mono gradient-text relative group inline-block'
        } else if (token.depth === 2) {
          headingStyle = `text-2.5xl font-bold tracking-tight mb-6 mt-12 ${isDark ? 'text-white' : 'text-gray-900'}`
        } else if (token.depth === 3) {
          headingStyle = `text-xl font-bold tracking-tight mb-4 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`
        } else {
          headingStyle = `text-lg font-bold tracking-tight mb-3 mt-6 ${isDark ? 'text-white' : 'text-gray-900'}`
        }

        return (
          <HeadingTag key={blockIdx} id={slug} className={headingStyle}>
            {renderInlineTokens(token.tokens)}
            {token.depth === 1 && (
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
            )}
          </HeadingTag>
        )
      }
      case 'paragraph':
        return (
          <p key={blockIdx} className={`text-sm leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {renderInlineTokens(token.tokens)}
          </p>
        )
      case 'code': {
        const langParts = (token.lang || '').split(/\s+/)
        const language = langParts[0] || 'python'
        const filename = langParts[1] || ''
        return (
          <div key={blockIdx} className="my-6">
            <CodeBlock language={language} filename={filename}>
              {token.text}
            </CodeBlock>
          </div>
        )
      }
      case 'list': {
        const ListTag = token.ordered ? 'ol' : 'ul'
        const listStyle = token.ordered 
          ? 'list-decimal pl-6 mb-6 space-y-2.5 text-sm'
          : 'list-disc pl-6 mb-6 space-y-2.5 text-sm'
        return (
          <ListTag key={blockIdx} className={`${listStyle} ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {token.items.map((item: any, itemIdx: number) => (
              <li key={itemIdx} className="leading-relaxed">
                {item.tokens && item.tokens.length > 0 ? item.tokens.map((child: any, childIdx: number) => {
                  if (child.type === 'paragraph' || child.type === 'text') {
                    return <span key={childIdx}>{renderInlineTokens(child.tokens)}</span>
                  }
                  return renderBlock(child, childIdx)
                }) : (item.text ? <span>{item.text}</span> : null)}
              </li>
            ))}
          </ListTag>
        )
      }
      case 'blockquote': {
        const alertData = parseAlert(token)
        if (alertData) {
          const { kind, title, cleanTokens } = alertData
          
          let alertStyles = ''
          let icon = null
          
          if (kind === 'tip') {
            alertStyles = 'border-l-4 border-aquilia-500 bg-aquilia-500/5 dark:bg-aquilia-950/20'
            icon = <Zap className="w-5 h-5 text-aquilia-500" />
          } else if (kind === 'warning') {
            alertStyles = 'border-l-4 border-amber-500 bg-amber-500/5 dark:bg-amber-950/20'
            icon = <AlertTriangle className="w-5 h-5 text-amber-500" />
          } else if (kind === 'important') {
            alertStyles = 'border-l-4 border-red-500 bg-red-500/5 dark:bg-red-950/20'
            icon = <AlertOctagon className="w-5 h-5 text-red-500" />
          } else {
            alertStyles = 'border-l-4 border-blue-500 bg-blue-500/5 dark:bg-blue-950/20'
            icon = <Info className="w-5 h-5 text-blue-500" />
          }
          
          return (
            <div key={blockIdx} className={`p-5 rounded-r-xl my-6 flex gap-4 ${alertStyles}`}>
              <div className="shrink-0 mt-0.5">{icon}</div>
              <div className="space-y-2 flex-grow">
                <span className={`font-bold text-xs uppercase tracking-wider block ${
                  kind === 'tip' ? 'text-aquilia-500' :
                  kind === 'warning' ? 'text-amber-500' :
                  kind === 'important' ? 'text-red-500' :
                  'text-blue-500'
                }`}>
                  {title}
                </span>
                <div className="space-y-2">
                  {cleanTokens.map((t, idx) => renderBlock(t, idx))}
                </div>
              </div>
            </div>
          )
        }

        return (
          <blockquote key={blockIdx} className={`pl-5 border-l-4 my-6 italic ${
            isDark ? 'border-zinc-800 text-gray-500' : 'border-zinc-200 text-gray-500'
          }`}>
            {token.tokens.map((t: any, idx: number) => renderBlock(t, idx))}
          </blockquote>
        )
      }
      case 'table': {
        return (
          <div key={blockIdx} className="overflow-x-auto my-8">
            <table className={`w-full text-sm text-left border-collapse ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <thead>
                <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                  {token.header.map((cell: any, cellIdx: number) => (
                    <th key={cellIdx} className="py-3 px-4 font-semibold text-aquilia-500 font-mono text-xs uppercase tracking-wider">
                      {renderInlineTokens(cell.tokens)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
                {token.rows.map((row: any[], rowIdx: number) => (
                  <tr key={rowIdx} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                    {row.map((cell: any, cellIdx: number) => (
                      <td key={cellIdx} className="py-3.5 px-4 leading-relaxed">
                        {renderInlineTokens(cell.tokens)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
      case 'text':
        return (
          <p key={blockIdx} className={`text-sm leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {token.tokens ? renderInlineTokens(token.tokens) : token.text}
          </p>
        )
      case 'def':
        return null
      case 'html':
        return (
          <div 
            key={blockIdx} 
            dangerouslySetInnerHTML={{ __html: token.text }} 
            className="markdown-html my-4"
          />
        )
      case 'space':
        return null
      case 'hr':
        return <hr key={blockIdx} className={`my-8 border-t ${isDark ? 'border-white/5' : 'border-zinc-200'}`} />
      default:
        return <div key={blockIdx}>{token.raw}</div>
    }
  }

  return (
    <div className="markdown-bridge space-y-4">
      {tokens.map((token, idx) => renderBlock(token, idx))}
    </div>
  )
}
