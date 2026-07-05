import { useState, useRef, useEffect, type FormEvent } from 'react'
import {
  X, Send, User, Loader2,
  Trash2, HelpCircle, BookOpen
} from 'lucide-react'
import { CodeBlock } from './CodeBlock'
import { useTheme } from '../context/ThemeContext'
import { docsContent } from '../data/docsContent'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: { title: string; path: string }[]
}

interface SearchResult {
  title: string
  path: string
  plainText: string
  score: number
}

// Simple TF-IDF/lexical client-side search helper
function searchDocs(query: string): SearchResult[] {
  const terms = query
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(/\s+/)
    .filter(t => t.length > 2)

  if (terms.length === 0) return []

  const results: SearchResult[] = []

  for (const doc of docsContent) {
    let score = 0
    const titleLower = doc.title.toLowerCase()
    const textLower = doc.plainText.toLowerCase()

    for (const term of terms) {
      // Exact title match weight
      if (titleLower.includes(term)) {
        score += 20
      }
      
      // Match count in title
      const titleMatches = (titleLower.match(new RegExp(term, 'g')) || []).length
      score += titleMatches * 10

      // Match count in text content
      const textMatches = (textLower.match(new RegExp(term, 'g')) || []).length
      score += textMatches * 1.5
    }

    if (score > 0) {
      results.push({
        title: doc.title,
        path: doc.path,
        plainText: doc.plainText,
        score
      })
    }
  }

  // Sort by score descending
  return results.sort((a, b) => b.score - a.score)
}

export function Chatbox() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hi! I am your Aquilia Framework Assistant. Ask me anything about the manifest-driven architecture, DI container, ORM, security, auth, background tasks, or any other part of the framework.',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [displayedText, setDisplayedText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const streamingTextRef = useRef('')

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Smooth typewriter streaming effect
  useEffect(() => {
    if (displayedText.length >= streamingTextRef.current.length && !isStreaming) {
      return
    }

    const timer = setTimeout(() => {
      const target = streamingTextRef.current
      const currentLength = displayedText.length
      if (currentLength < target.length) {
        // Appending 3 characters at a time for smooth but fast typewriter updates
        const step = Math.min(3, target.length - currentLength)
        const nextChunk = target.slice(0, currentLength + step)
        setDisplayedText(nextChunk)
        
        setMessages(prev => {
          const updated = [...prev]
          const lastMsg = updated[updated.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            updated[updated.length - 1] = {
              ...lastMsg,
              content: nextChunk
            }
          }
          return updated
        })
      }
    }, 15)

    return () => clearTimeout(timer)
  }, [displayedText, isStreaming])



  const handleClear = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Hi! I am your Aquilia Framework Assistant. Ask me anything about the manifest-driven architecture, DI container, ORM, security, auth, background tasks, or any other part of the framework.',
        timestamp: new Date()
      }
    ])
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    // Add user message to state
    const newMsg: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, newMsg])

    // Find relevant documentation pages
    const searchResults = searchDocs(userMessage)
    const topResults = searchResults.slice(0, 3)
    
    // Build context
    let contextStr = ''
    if (topResults.length > 0) {
      contextStr = topResults
        .map(
          (res, idx) =>
            `[Source #${idx + 1}: ${res.title} (Path: ${res.path})]\n${res.plainText.substring(0, 1500)}...`
        )
        .join('\n\n')
    }

    const systemPrompt = `You are the Aquilia AI Documentation Assistant, a premium, knowledgeable agent designed to answer developer queries about the Aquilia async Python web framework.
Use the documentation context provided below to guide your response. Always write production-grade, clean, and modern Python or react code.
Preserve architectural concepts like auto-discovery, AppManifest, Workspace configuration, async dependency injection containers, ORM models, typed faults, etc.
If the context does not contain the exact answer, you can supplement with general knowledge of Python, but keep the tone authoritative, technical, and helpful.
Format your responses beautifully in markdown. If you output code blocks, specify the correct language (e.g., python, typescript, bash, yaml, json) so that the syntax highlighter works correctly. Keep explanations concise but technically accurate.`

    const userContent = `Here is my question: "${userMessage}"\n\n` + 
      (contextStr ? `Here is the relevant Aquilia documentation context:\n${contextStr}` : `No direct documentation search results were found for this query.`)

    // Determine OpenRouter configs
    const apiKey = import.meta.env.VITE_OPENROUTER_API_KEY || ''
    const baseURL = import.meta.env.VITE_OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1'
    const model = import.meta.env.VITE_OPENROUTER_MODEL || 'google/gemini-2.5-flash'

    if (!apiKey) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '⚠️ **OpenRouter API Key is missing.**\n\nPlease configure it inside the `aqdocx/.env` file as `VITE_OPENROUTER_API_KEY`.',
          timestamp: new Date()
        }
      ])
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(`${baseURL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'HTTP-Referer': 'https://aquilia.dev',
          'X-Title': 'Aquilia Docs Assistant'
        },
        body: JSON.stringify({
          model: model,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userContent }
          ],
          temperature: 0.2,
          stream: true
        })
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          sources: topResults.map(r => ({ title: r.title, path: r.path }))
        }
      ])
      setIsLoading(false)

      const reader = response.body?.getReader()
      const decoder = new TextDecoder('utf-8')
      let done = false
      let buffer = ''

      setIsStreaming(true)
      streamingTextRef.current = ''
      setDisplayedText('')

      if (reader) {
        while (!done) {
          const { value, done: readerDone } = await reader.read()
          done = readerDone
          if (value) {
            buffer += decoder.decode(value, { stream: !done })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              const trimmed = line.trim()
              if (!trimmed) continue
              if (trimmed === 'data: [DONE]') {
                done = true
                break
              }
              if (trimmed.startsWith('data: ')) {
                const jsonStr = trimmed.slice(6)
                try {
                  const parsed = JSON.parse(jsonStr)
                  const content = parsed.choices?.[0]?.delta?.content || ''
                  if (content) {
                    streamingTextRef.current += content
                  }
                } catch (e) {
                  // Ignore partial parsing errors
                }
              }
            }
          }
        }

        if (buffer) {
          const trimmed = buffer.trim()
          if (trimmed.startsWith('data: ') && trimmed !== 'data: [DONE]') {
            const jsonStr = trimmed.slice(6)
            try {
              const parsed = JSON.parse(jsonStr)
              const content = parsed.choices?.[0]?.delta?.content || ''
              if (content) {
                streamingTextRef.current += content
              }
            } catch (e) {
              // Ignore
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ **Error communicating with OpenRouter:**\n\n${err.message || 'Unknown network error. Please verify your API URL, key, and model choice.'}`,
          timestamp: new Date()
        }
      ])
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
    }
  }

  // Helper to render inline formatting
  const renderTextWithInlineFormatting = (text: string) => {
    const inlineParts = text.split(/(\*\*.*?\*\*|`.*?`)/g)
    return inlineParts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="px-1.5 py-0.5 rounded bg-white/10 text-aquilia-400 font-mono text-[11px]">{part.slice(1, -1)}</code>
      }
      return part
    })
  }

  // Custom Markdown parser rendering logic
  const parseMarkdown = (text: string) => {
    let processedText = text
    const occurrences = (text.match(/```/g) || []).length
    if (occurrences % 2 !== 0) {
      if (!text.endsWith('\n')) {
        processedText += '\n'
      }
      processedText += '```'
    }

    // Split by block code tags
    const parts = processedText.split(/(```[a-z]*\n[\s\S]*?\n```)/g)
    return parts.map((part, index) => {
      if (part.startsWith('```')) {
        const match = part.match(/```([a-z]*)\n([\s\S]*?)\n```/)
        const lang = match ? match[1] : 'python'
        const code = match ? match[2] : part.slice(3, -3)
        return (
          <div key={index} className="my-3">
            <CodeBlock language={lang} compact={true} showLineNumbers={false}>
              {code}
            </CodeBlock>
          </div>
        )
      } else {
        const lines = part.split('\n')
        return (
          <div key={index} className="space-y-1.5 my-1 text-sm leading-relaxed">
            {lines.map((line, lineIndex) => {
              const trimmed = line.trim()
              if (!trimmed) return <div key={lineIndex} className="h-2" />

              // Bullet lists
              if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                return (
                  <li key={lineIndex} className="ml-4 list-disc pl-1 text-gray-300">
                    {renderTextWithInlineFormatting(trimmed.substring(2))}
                  </li>
                )
              }
              // Numbered lists
              if (/^\d+\.\s/.test(trimmed)) {
                const listText = trimmed.replace(/^\d+\.\s/, '')
                return (
                  <li key={lineIndex} className="ml-4 list-decimal pl-1 text-gray-300">
                    {renderTextWithInlineFormatting(listText)}
                  </li>
                )
              }
              // Headers
              if (trimmed.startsWith('### ')) {
                return (
                  <h4 key={lineIndex} className="font-bold text-sm mt-3 mb-1 text-white border-b border-white/5 pb-0.5">
                    {renderTextWithInlineFormatting(trimmed.substring(4))}
                  </h4>
                )
              }
              if (trimmed.startsWith('## ')) {
                return (
                  <h3 key={lineIndex} className="font-bold text-base mt-4 mb-2 text-white">
                    {renderTextWithInlineFormatting(trimmed.substring(3))}
                  </h3>
                )
              }
              if (trimmed.startsWith('# ')) {
                return (
                  <h2 key={lineIndex} className="font-bold text-lg mt-5 mb-2 text-white">
                    {renderTextWithInlineFormatting(trimmed.substring(2))}
                  </h2>
                )
              }

              return <p key={lineIndex} className="text-gray-300">{renderTextWithInlineFormatting(line)}</p>
            })}
          </div>
        )
      }
    })
  }

  const suggestions = [
    'How do I install Aquilia?',
    'Show me a basic Module manifest definition',
    'How does Dependency Injection resolution work?',
    'How to declare database ORM Models and run migrations?',
    'Configure background tasks with workers'
  ]

  return (
    <>
      {/* Circular Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer shadow-lg hover:scale-105 active:scale-95 group border ${
          isDark
            ? 'bg-zinc-900 hover:bg-zinc-800 border-white/10'
            : 'bg-white hover:bg-gray-50 border-gray-200'
        }`}
        title="Chat with AI Assistant"
        style={{
          boxShadow: isDark
            ? '0 10px 30px -10px rgba(0, 0, 0, 0.7), 0 0 20px rgba(255, 255, 255, 0.05)'
            : '0 10px 30px -10px rgba(0, 0, 0, 0.15)'
        }}
      >
        <span className="relative flex h-full w-full items-center justify-center">
          <img
            src="/logo.png"
            alt="Aquilia Logo"
            className="w-8 h-8 object-contain transition-transform duration-300 group-hover:rotate-12 rounded-xl"
          />
        </span>
      </button>

      {/* Premium Chatbox Panel */}
      <div
        className={`fixed bottom-24 right-6 w-100 max-w-[calc(100vw-2rem)] h-[620px] max-h-[calc(100vh-8rem)] z-50 rounded-3xl flex flex-col overflow-hidden shadow-2xl transition-all duration-300 transform origin-bottom-right ${
          isOpen
            ? 'scale-100 opacity-100 translate-y-0 pointer-events-auto'
            : 'scale-90 opacity-0 translate-y-4 pointer-events-none'
        } ${isDark ? 'bg-zinc-950/90 border border-white/10' : 'bg-white/95 border border-gray-200'}`}
        style={{
          backdropFilter: 'blur(20px)',
          boxShadow: isDark
            ? '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 40px rgba(34, 197, 94, 0.05)'
            : '0 25px 50px -12px rgba(0, 0, 0, 0.15)'
        }}
      >
        {/* Chatbox Header */}
        <div className={`p-4 flex items-center justify-between border-b ${isDark ? 'border-white/5 bg-white/[0.02]' : 'border-gray-200 bg-gray-50/50'}`}>
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Aquilia Logo" className="w-8 h-8 object-contain rounded-lg" />
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className={`font-bold text-sm leading-none ${isDark ? 'text-white' : 'text-gray-900'}`}>Aquilia AI Assistant</h3>
              </div>
              <span className={`text-[10px] uppercase tracking-wider font-semibold font-mono ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                Docs Context Agent
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={handleClear}
              className={`p-2 rounded-xl transition-colors cursor-pointer ${isDark ? 'text-gray-400 hover:text-white hover:bg-white/10' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'}`}
              title="Clear chat history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className={`p-2 rounded-xl transition-colors cursor-pointer ${isDark ? 'text-gray-400 hover:text-white hover:bg-white/10' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'}`}
              title="Minimize chat"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>



        {/* Chat History Viewport */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 min-w-0 ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse max-w-[85%]' : 'mr-auto w-full'
              }`}
            >
              {/* Avatar Icon */}
              {msg.role === 'user' ? (
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border ${
                    isDark ? 'bg-aquilia-950/20 border-aquilia-500/30' : 'bg-aquilia-50 border-aquilia-200'
                  }`}
                >
                  <User className="w-4 h-4 text-aquilia-400" />
                </div>
              ) : (
                <img src="/logo.png" alt="Bot Logo" className="w-8 h-8 object-contain rounded-lg shrink-0" />
              )}

              {/* Text Bubble / Content */}
              <div className="flex flex-col gap-1.5 min-w-0 flex-1">
                {msg.role === 'user' ? (
                  <div
                    className={`p-3.5 rounded-2xl rounded-tr-none text-sm text-white ${
                      isDark ? 'bg-aquilia-900/30 border border-aquilia-500/20' : 'bg-aquilia-600'
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  </div>
                ) : (
                  <div className={`text-sm leading-relaxed min-w-0 w-full ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    <div className="markdown-body w-full overflow-hidden break-words">
                      {parseMarkdown(msg.content)}
                    </div>
                  </div>
                )}

                {/* Sources list */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-1 px-1">
                    <span className={`text-[10px] font-semibold flex items-center gap-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <BookOpen className="w-3 h-3" /> Related docs:
                    </span>
                    {msg.sources.map((src, idx) => (
                      <span
                        key={idx}
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-lg border ${
                          isDark
                            ? 'bg-zinc-900/50 border-white/5 text-gray-400 hover:text-aquilia-400 hover:border-aquilia-400/20'
                            : 'bg-gray-100 border-gray-200 text-gray-600 hover:text-aquilia-600 hover:border-aquilia-300'
                        } cursor-help transition-all`}
                        title={`Path: ${src.path}`}
                      >
                        {src.title}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3 w-full mr-auto items-center text-xs text-gray-400 pl-1">
              <img src="/logo.png" alt="Bot Logo" className="w-8 h-8 object-contain rounded-lg shrink-0" />
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-aquilia-400 shrink-0" />
                <span>Searching documentation and preparing response...</span>
              </div>
            </div>
          )}

          {/* Suggested Prompts (Chips) */}
          {messages.length === 1 && (
            <div className="pt-2 space-y-2">
              <div className={`text-xs font-semibold flex items-center gap-1.5 px-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <HelpCircle className="w-3.5 h-3.5 text-aquilia-500" />
                <span>Suggested topics:</span>
              </div>
              <div className="flex flex-col gap-2">
                {suggestions.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSuggestionClick(s)}
                    className={`w-full text-left text-xs p-3 rounded-2xl border transition-all cursor-pointer ${
                      isDark
                        ? 'bg-zinc-900/30 border-white/5 text-gray-300 hover:bg-aquilia-950/20 hover:border-aquilia-500/30 hover:text-white'
                        : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-aquilia-300 hover:text-gray-900'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar Form */}
        <form
          onSubmit={handleSendMessage}
          className={`p-3.5 border-t flex items-center gap-2 ${
            isDark ? 'border-white/5 bg-black/40' : 'border-gray-200 bg-gray-50/50'
          }`}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about Aquilia..."
            className={`flex-1 px-4 py-2.5 text-sm rounded-2xl outline-none border focus:border-aquilia-500 ${
              isDark
                ? 'bg-zinc-900 border-white/10 text-white placeholder-gray-500'
                : 'bg-white border-gray-300 text-black placeholder-gray-400'
            }`}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`p-2.5 rounded-2xl flex items-center justify-center transition-all cursor-pointer ${
              !input.trim() || isLoading
                ? `${isDark ? 'text-gray-600 bg-white/[0.02]' : 'text-gray-400 bg-gray-100'}`
                : 'bg-aquilia-600 text-white hover:bg-aquilia-500 hover:scale-105 active:scale-95'
            }`}
            style={{
              boxShadow: input.trim() && !isLoading ? '0 0 10px rgba(34, 197, 94, 0.2)' : 'none'
            }}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </>
  )
}
