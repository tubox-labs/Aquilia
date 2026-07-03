import { useCallback, useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { Highlight, type PrismLib } from 'prism-react-renderer'
import Prism from 'prismjs'
import { aquiliaDarkTheme, aquiliaLightTheme } from '../../lib/prismThemes'

interface SignatureLineProps {
  code: string
  language?: string
  isDark: boolean
}

/**
 * A slim, chrome-free syntax-highlighted line for entity signatures — deliberately
 * lighter than the full `CodeBlock` (no header, no traffic lights) so it reads as a
 * single typographic element inside the hover panel rather than a nested "card".
 */
export function SignatureLine({ code, language = 'python', isDark }: SignatureLineProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }, [code])

  return (
    <div
      className={`group/sig relative flex items-start gap-2 rounded-lg border px-3 py-2.5 ${isDark ? 'bg-black/40 border-white/10' : 'bg-gray-50 border-gray-200'
        }`}
    >
      <Highlight prism={Prism as unknown as PrismLib} theme={isDark ? aquiliaDarkTheme : aquiliaLightTheme} code={code} language={language}>
        {({ tokens, getLineProps, getTokenProps }) => (
          <pre className="flex-1 overflow-x-auto font-mono text-[12.5px] leading-relaxed bg-transparent">
            {tokens.map((line, i) => (
              <div key={i} {...getLineProps({ line })}>
                {line.map((token, key) => (
                  <span key={key} {...getTokenProps({ token })} />
                ))}
              </div>
            ))}
          </pre>
        )}
      </Highlight>
      <button
        type="button"
        onClick={handleCopy}
        aria-label={copied ? 'Copied signature' : 'Copy signature'}
        className={`shrink-0 mt-0.5 p-1 rounded-md opacity-0 group-hover/sig:opacity-100 focus-visible:opacity-100 transition-opacity ${copied
          ? 'text-aquilia-400'
          : isDark
            ? 'text-gray-500 hover:text-white hover:bg-white/10'
            : 'text-gray-400 hover:text-gray-700 hover:bg-gray-200'
          }`}
      >
        {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
      </button>
    </div>
  )
}
