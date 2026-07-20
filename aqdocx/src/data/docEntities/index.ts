/**
 * Side-effect barrel: importing this module registers every doc-entity dataset in
 * this folder. Loaded once from `App.tsx` so `<DocTerm>` works app-wide regardless of
 * which page mounts first. New pages that want their own entities should add a file
 * here and export it the same way — `registerDocEntities([...])` at module scope.
 */
import './serverLifecycle'
import './showcase'
import './adminPanel'
import './configEntities'
import './requestResponse'
import './controllers'
import './ormEntities'
import './dbEntities'
import './contractEntities'
import './diEntities'
import './authEntities'
import './sessionsEntities'
import './subsystemEntities'
import './cliEntities'
import './testingEntities'
import './speculaEntities'
import './aquiliaEntities'
import './cacheHttpI18n'
import './websocketsTemplatesMail'
import './providers'
