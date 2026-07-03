import type { DocEntityData } from './types'

/**
 * Global, module-scoped registry of documentation entities. Populated via side-effect
 * imports of `src/data/docEntities/*` files (or any page-local data). `DocTerm` looks
 * entities up by id at render time — nothing here is React state, so registration is
 * cheap and can happen from anywhere, in any order, including lazily-loaded routes.
 */
const registry = new Map<string, DocEntityData>()

const listeners = new Set<() => void>()

/** Register one or more entities. Re-registering an id overwrites the previous entry. */
export function registerDocEntities(entities: DocEntityData | DocEntityData[]): void {
  const list = Array.isArray(entities) ? entities : [entities]
  for (const entity of list) {
    if (!entity?.id) continue
    registry.set(entity.id, entity)
  }
  if (list.length) {
    for (const listener of listeners) listener()
  }
}

export function getDocEntity(id: string): DocEntityData | undefined {
  return registry.get(id)
}

export function hasDocEntity(id: string): boolean {
  return registry.has(id)
}

export function getAllDocEntities(): DocEntityData[] {
  return [...registry.values()]
}

/** Subscribe to registry changes (used by lazily-loaded doc pages registering after mount). */
export function subscribeDocRegistry(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
