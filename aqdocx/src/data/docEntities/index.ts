/**
 * Side-effect barrel: importing this module registers every doc-entity dataset in
 * this folder. Loaded once from `App.tsx` so `<DocTerm>` works app-wide regardless of
 * which page mounts first. New pages that want their own entities should add a file
 * here and export it the same way — `registerDocEntities([...])` at module scope.
 */
import './serverLifecycle'
import './showcase'
