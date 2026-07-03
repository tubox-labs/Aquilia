import type { PrismTheme } from 'prism-react-renderer'

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
 *
 * Shared between `CodeBlock` and the doc-preview `SignatureLine` so both surfaces
 * highlight code identically.
 */
export const aquiliaDarkTheme: PrismTheme = {
  plain: { color: '#e5e7eb', backgroundColor: '#000000' },
  styles: [
    { types: ['comment', 'prolog', 'doctype', 'cdata'], style: { color: '#6b7280', fontStyle: 'italic' as const } },
    { types: ['keyword', 'builtin', 'tag', 'selector', 'important'], style: { color: '#22c55e' } },
    { types: ['string', 'char', 'attr-value', 'template-string', 'template-punctuation'], style: { color: '#4ade80' } },
    { types: ['number', 'boolean', 'constant'], style: { color: '#60a5fa' } },
    { types: ['function', 'function-variable'], style: { color: '#fde047' } },
    { types: ['class-name', 'maybe-class-name'], style: { color: '#03eb26' } },
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

export const aquiliaLightTheme: PrismTheme = {
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
