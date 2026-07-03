/**
 * Data contracts for the Documentation Hover Preview System.
 *
 * Any documentation entity (function, hook, class, decorator, model, CLI command,
 * endpoint, type, etc.) can be described with a `DocEntityData` object and registered
 * via `registerDocEntities()`. Once registered, wrapping the entity's name anywhere in
 * the docs with `<DocTerm id="...">` automatically gains the hover/focus preview.
 */

export type DocEntityType =
  | 'function'
  | 'method'
  | 'hook'
  | 'class'
  | 'decorator'
  | 'model'
  | 'component'
  | 'event'
  | 'config'
  | 'cli'
  | 'endpoint'
  | 'type'

export type DocEntityStatus = 'stable' | 'beta' | 'experimental' | 'deprecated'

export type DocNoteKind = 'note' | 'warning' | 'tip'

export interface DocEntityParam {
  name: string
  type?: string
  description?: string
  optional?: boolean
  default?: string
}

export interface DocEntityReturn {
  type?: string
  description?: string
}

export interface DocEntityExample {
  code: string
  language?: string
  title?: string
}

export interface DocEntityRelated {
  /** Id of another registered entity. Renders as an in-panel jump; falls back to a plain label if unregistered. */
  id?: string
  label: string
  /** Optional explicit navigation target if this related item isn't (yet) a registered entity. */
  href?: string
}

export interface DocEntityNote {
  kind?: DocNoteKind
  text: string
}

export interface DocEntityDeprecation {
  since?: string
  message?: string
  replacement?: string
}

export interface DocEntitySource {
  file: string
  line?: number
  href?: string
}

export interface DocEntityData {
  id: string
  type: DocEntityType
  title: string
  description: string
  signature?: string
  /** Prism language for `signature` and `example`. Defaults to "python". */
  language?: string
  parameters?: DocEntityParam[]
  returns?: DocEntityReturn
  example?: DocEntityExample
  related?: DocEntityRelated[]
  status?: DocEntityStatus
  version?: string
  deprecated?: DocEntityDeprecation
  notes?: DocEntityNote[]
  /** Link to the full documentation page for this entity. */
  docsHref?: string
  source?: DocEntitySource
}
