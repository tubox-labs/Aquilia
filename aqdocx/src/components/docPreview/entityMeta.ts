import {
  Box,
  Braces,
  Component,
  Cog,
  Database,
  FunctionSquare,
  Globe,
  Radio,
  Terminal,
  Wand2,
  Zap,
  type LucideIcon,
} from 'lucide-react'
import type { DocEntityType } from '../../lib/docPreview/types'

interface EntityMeta {
  label: string
  icon: LucideIcon
  /** Tailwind-friendly color tokens, theme-aware via [isDark] variants applied at call site. */
  dark: { text: string; bg: string; border: string }
  light: { text: string; bg: string; border: string }
}

const DEFAULT_META: EntityMeta = {
  label: 'Reference',
  icon: Braces,
  dark: { text: 'text-gray-300', bg: 'bg-white/5', border: 'border-white/10' },
  light: { text: 'text-gray-600', bg: 'bg-gray-100', border: 'border-gray-200' },
}

const ENTITY_META: Record<DocEntityType, EntityMeta> = {
  function: {
    label: 'Function',
    icon: FunctionSquare,
    dark: { text: 'text-amber-300', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
    light: { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' },
  },
  method: {
    label: 'Method',
    icon: FunctionSquare,
    dark: { text: 'text-cyan-300', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
    light: { text: 'text-cyan-700', bg: 'bg-cyan-50', border: 'border-cyan-200' },
  },
  hook: {
    label: 'Lifecycle Hook',
    icon: Zap,
    dark: { text: 'text-aquilia-300', bg: 'bg-aquilia-500/10', border: 'border-aquilia-500/20' },
    light: { text: 'text-aquilia-700', bg: 'bg-aquilia-50', border: 'border-aquilia-200' },
  },
  class: {
    label: 'Class',
    icon: Box,
    dark: { text: 'text-orange-300', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
    light: { text: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-200' },
  },
  decorator: {
    label: 'Decorator',
    icon: Wand2,
    dark: { text: 'text-aquilia-300', bg: 'bg-aquilia-500/10', border: 'border-aquilia-500/20' },
    light: { text: 'text-aquilia-700', bg: 'bg-aquilia-50', border: 'border-aquilia-200' },
  },
  model: {
    label: 'Model',
    icon: Database,
    dark: { text: 'text-blue-300', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    light: { text: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-200' },
  },
  component: {
    label: 'Component',
    icon: Component,
    dark: { text: 'text-violet-300', bg: 'bg-violet-500/10', border: 'border-violet-500/20' },
    light: { text: 'text-violet-700', bg: 'bg-violet-50', border: 'border-violet-200' },
  },
  event: {
    label: 'Event',
    icon: Radio,
    dark: { text: 'text-pink-300', bg: 'bg-pink-500/10', border: 'border-pink-500/20' },
    light: { text: 'text-pink-700', bg: 'bg-pink-50', border: 'border-pink-200' },
  },
  config: {
    label: 'Configuration',
    icon: Cog,
    dark: { text: 'text-slate-300', bg: 'bg-slate-500/10', border: 'border-slate-500/20' },
    light: { text: 'text-slate-700', bg: 'bg-slate-100', border: 'border-slate-200' },
  },
  cli: {
    label: 'CLI Command',
    icon: Terminal,
    dark: { text: 'text-emerald-300', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
    light: { text: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' },
  },
  endpoint: {
    label: 'API Endpoint',
    icon: Globe,
    dark: { text: 'text-sky-300', bg: 'bg-sky-500/10', border: 'border-sky-500/20' },
    light: { text: 'text-sky-700', bg: 'bg-sky-50', border: 'border-sky-200' },
  },
  type: {
    label: 'Type',
    icon: Braces,
    dark: { text: 'text-fuchsia-300', bg: 'bg-fuchsia-500/10', border: 'border-fuchsia-500/20' },
    light: { text: 'text-fuchsia-700', bg: 'bg-fuchsia-50', border: 'border-fuchsia-200' },
  },
}

export function getEntityMeta(type: DocEntityType): EntityMeta {
  return ENTITY_META[type] ?? DEFAULT_META
}
