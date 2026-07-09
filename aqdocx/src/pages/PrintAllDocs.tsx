import { useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { IntroductionPage } from './docs/getting-started/Introduction'
import { InstallationPage } from './docs/getting-started/Installation'
import { QuickStartPage } from './docs/getting-started/QuickStart'
import { DeveloperGuidePage } from './docs/getting-started/DeveloperGuide'
import { ArchitecturePage } from './docs/getting-started/Architecture'
import { ProjectStructurePage } from './docs/getting-started/ProjectStructure'
import { AdminSetupPage } from './docs/getting-started/AdminSetup'
import { ServerOverview } from './docs/server/Overview'
import { ServerASGI } from './docs/server/ASGI'
import { ServerLifecycle } from './docs/server/Lifecycle'
import { ConfigOverview } from './docs/config/Overview'
import { ConfigWorkspace } from './docs/config/Workspace'
import { ConfigModule } from './docs/config/Module'
import { ConfigManifest } from './docs/config/Manifest'
import { RequestPage } from './docs/request-response/Request'
import { ResponsePage } from './docs/request-response/Response'
import { ControllersOverview } from './docs/controllers/Overview'
import { ControllersRequestCtx } from './docs/controllers/RequestCtx'
import { RoutingOverview } from './docs/routing/Overview'
import { DIOverview } from './docs/di/Overview'
import { DIContainer } from './docs/di/Container'
import { ModelsOverview } from './docs/models/Overview'
import { ModelsQuerySet } from './docs/models/QuerySet'
import { BlueprintsOverview } from './docs/blueprints/Overview'
import { DatabaseOverview } from './docs/database/Overview'
import { AuthOverview } from './docs/auth/Overview'
import { SessionsOverview } from './docs/sessions/Overview'
import { MiddlewareOverview } from './docs/middleware/Overview'
import { FaultsOverview } from './docs/faults/Overview'
import { FaultsTaxonomy } from './docs/faults/Taxonomy'
import { FaultsEngine } from './docs/faults/Engine'
import { FaultsHandlers } from './docs/faults/Handlers'
import { CacheOverview } from './docs/cache/Overview'
import { HTTPOverview } from './docs/http/Overview'
import { EffectsOverview } from './docs/subsystem/Overview'
import { EffectsDBTx } from './docs/subsystem/DBTx'
import { EffectsCacheEffect } from './docs/subsystem/CacheEffect'
import { EffectsQueueEffect } from './docs/subsystem/QueueEffect'
import { EffectsHTTPEffect } from './docs/subsystem/HTTPEffect'
import { EffectsStorageEffect } from './docs/subsystem/StorageEffect'
import { EffectsCustomEffects } from './docs/subsystem/CustomEffects'
import { FlowPipelines } from './docs/subsystem/Pipelines'
import { FlowContextNodes } from './docs/subsystem/ContextNodes'
import { FlowLayers } from './docs/subsystem/Layers'
import { SSEOverview } from './docs/sse/Overview'
import { SSEStandardEvents } from './docs/sse/StandardEvents'
import { SSETextJsonStreams } from './docs/sse/TextJsonStreams'
import { SSEOpenAIStreaming } from './docs/sse/OpenAIStreaming'
import { SSEResourceManagement } from './docs/sse/ResourceManagement'
import { AquilaryOverview } from './docs/aquilary/Overview'
import { AquilaryManifest } from './docs/aquilary/Manifest'
import { AquilaryRuntime } from './docs/aquilary/Runtime'
import { Releases } from './Releases'
import { Changelogs } from './Changelogs'

export function PrintAllDocs() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  useEffect(() => {
    // Delay slightly to allow rendering to complete before triggering print
    const timer = setTimeout(() => {
      window.print()
    }, 1500)

    // Close the print tab after printing/cancelling
    window.onafterprint = () => {
      window.close()
    }

    return () => clearTimeout(timer)
  }, [])

  return (
    <div className={`min-h-screen py-16 px-8 max-w-5xl mx-auto ${isDark ? 'bg-black text-white' : 'bg-white text-gray-900'}`}>
      <style>{`
        @media print {
          body {
            background-color: white !important;
            color: black !important;
          }
          .print-page-break {
            page-break-after: always;
            break-after: page;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>
      
      <div className="text-center mb-16 no-print">
        <h1 className="text-3xl font-bold mb-4">Compiling Entire Documentation...</h1>
        <p className="text-gray-400">The print dialog will automatically open. Once complete, this tab will close.</p>
      </div>

      <div className="space-y-16">
        <div className="print-page-break"><IntroductionPage /></div>
        <div className="print-page-break"><InstallationPage /></div>
        <div className="print-page-break"><QuickStartPage /></div>
        <div className="print-page-break"><DeveloperGuidePage /></div>
        <div className="print-page-break"><ArchitecturePage /></div>
        <div className="print-page-break"><ProjectStructurePage /></div>
        <div className="print-page-break"><AdminSetupPage /></div>
        <div className="print-page-break"><ServerOverview /></div>
        <div className="print-page-break"><ServerASGI /></div>
        <div className="print-page-break"><ServerLifecycle /></div>
        <div className="print-page-break"><ConfigOverview /></div>
        <div className="print-page-break"><ConfigWorkspace /></div>
        <div className="print-page-break"><ConfigModule /></div>
        <div className="print-page-break"><ConfigManifest /></div>
        <div className="print-page-break"><RequestPage /></div>
        <div className="print-page-break"><ResponsePage /></div>
        <div className="print-page-break"><ControllersOverview /></div>
        <div className="print-page-break"><ControllersRequestCtx /></div>
        <div className="print-page-break"><RoutingOverview /></div>
        <div className="print-page-break"><DIOverview /></div>
        <div className="print-page-break"><DIContainer /></div>
        <div className="print-page-break"><ModelsOverview /></div>
        <div className="print-page-break"><ModelsQuerySet /></div>
        <div className="print-page-break"><BlueprintsOverview /></div>
        <div className="print-page-break"><DatabaseOverview /></div>
        <div className="print-page-break"><AuthOverview /></div>
        <div className="print-page-break"><SessionsOverview /></div>
        <div className="print-page-break"><MiddlewareOverview /></div>
        <div className="print-page-break"><FaultsOverview /></div>
        <div className="print-page-break"><FaultsTaxonomy /></div>
        <div className="print-page-break"><FaultsEngine /></div>
        <div className="print-page-break"><FaultsHandlers /></div>
        <div className="print-page-break"><CacheOverview /></div>
        <div className="print-page-break"><HTTPOverview /></div>
        <div className="print-page-break"><EffectsOverview /></div>
        <div className="print-page-break"><FlowPipelines /></div>
        <div className="print-page-break"><FlowContextNodes /></div>
        <div className="print-page-break"><FlowLayers /></div>
        <div className="print-page-break"><SSEOverview /></div>
        <div className="print-page-break"><SSEStandardEvents /></div>
        <div className="print-page-break"><SSETextJsonStreams /></div>
        <div className="print-page-break"><SSEOpenAIStreaming /></div>
        <div className="print-page-break"><SSEResourceManagement /></div>
        <div className="print-page-break"><EffectsDBTx /></div>
        <div className="print-page-break"><EffectsCacheEffect /></div>
        <div className="print-page-break"><EffectsQueueEffect /></div>
        <div className="print-page-break"><EffectsHTTPEffect /></div>
        <div className="print-page-break"><EffectsStorageEffect /></div>
        <div className="print-page-break"><EffectsCustomEffects /></div>
        <div className="print-page-break"><AquilaryOverview /></div>
        <div className="print-page-break"><AquilaryManifest /></div>
        <div className="print-page-break"><AquilaryRuntime /></div>
        <div className="print-page-break">
          <h1 className="text-4xl font-bold mb-8">Releases &amp; Changelogs</h1>
          <Releases />
        </div>
        <div>
          <Changelogs />
        </div>
      </div>
    </div>
  )
}
