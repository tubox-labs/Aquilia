import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  Gauge,
  Network,
  Rocket,
  Server,
} from 'lucide-react'
import { Navbar } from '../components/Navbar'
import { Sidebar } from '../components/Sidebar'
import { useTheme } from '../context/ThemeContext'

interface ScenarioMetric {
  scenario: string
  requests: number
  throughputRps: number
  p50Ms: number
  p95Ms: number
  p99Ms: number
  failures: number
  avgCpuPercent: number
  peakRssMb: number
}

interface WebSocketMetric {
  supported: boolean
  skipped: boolean
  reason?: string
  connections?: number
  messages?: number
  throughputMsgsPerSec?: number
  p95Ms?: number
  failures?: number
}

interface FrameworkBenchmark {
  name: 'aquilia' | 'fastapi' | 'flask'
  startupSeconds: number
  summary: {
    meanThroughputRps: number
    meanP95Ms: number
    failureRatePercent: number
  }
  websocket: WebSocketMetric
  scenarios: ScenarioMetric[]
}

interface BenchmarkRun {
  runId: string
  generatedAt: string
  environment: {
    platform: string
    python: string
    cpuCores: number
  }
  methodology: string[]
  profile: {
    baseRequests: number
    concurrency: number
    warmup: number
  }
  frameworks: FrameworkBenchmark[]
}

const benchmarkRun: BenchmarkRun = {
  runId: '20260405-054915',
  generatedAt: '2026-04-05T05:53:17.967494+00:00',
  environment: {
    platform: 'macOS-26.3.1-arm64-arm-64bit-Mach-O',
    python: '3.14.3',
    cpuCores: 10,
  },
  methodology: [
    'All frameworks ran with a single server process via Uvicorn on localhost.',
    'Each HTTP scenario used scenario-specific warmup, then measured throughput and latency percentiles.',
    'CPU and RSS memory were sampled during each scenario.',
    'WebSocket benchmark used echo round trips where supported.',
    'Flask is treated as WebSocket unsupported in this suite (no extra extension stack).',
  ],
  profile: {
    baseRequests: 1200,
    concurrency: 48,
    warmup: 120,
  },
  frameworks: [
    {
      name: 'aquilia',
      startupSeconds: 0.4787,
      summary: {
        meanThroughputRps: 357.82,
        meanP95Ms: 374.43,
        failureRatePercent: 0,
      },
      websocket: {
        supported: true,
        skipped: false,
        connections: 12,
        messages: 960,
        throughputMsgsPerSec: 17387.71,
        p95Ms: 0.61,
        failures: 0,
      },
      scenarios: [
        { scenario: 'health', requests: 1200, throughputRps: 242.66, p50Ms: 150.15, p95Ms: 528.71, p99Ms: 782.34, failures: 0, avgCpuPercent: 2.15, peakRssMb: 85.06 },
        { scenario: 'json_simple', requests: 1200, throughputRps: 242.16, p50Ms: 140.33, p95Ms: 527.86, p99Ms: 868.44, failures: 0, avgCpuPercent: 2.05, peakRssMb: 76.3 },
        { scenario: 'json_large', requests: 720, throughputRps: 361.02, p50Ms: 42.17, p95Ms: 435.86, p99Ms: 738.22, failures: 0, avgCpuPercent: 30.09, peakRssMb: 77.56 },
        { scenario: 'di_chain', requests: 1200, throughputRps: 243.5, p50Ms: 141.32, p95Ms: 568.1, p99Ms: 862.2, failures: 0, avgCpuPercent: 2.13, peakRssMb: 77.56 },
        { scenario: 'middleware_stack', requests: 1080, throughputRps: 251.98, p50Ms: 135.5, p95Ms: 503.49, p99Ms: 740.71, failures: 0, avgCpuPercent: 2.17, peakRssMb: 64.7 },
        { scenario: 'route_static', requests: 1080, throughputRps: 250.8, p50Ms: 137.08, p95Ms: 510.34, p99Ms: 820.84, failures: 0, avgCpuPercent: 2.22, peakRssMb: 64.73 },
        { scenario: 'route_params', requests: 1080, throughputRps: 249.51, p50Ms: 139.98, p95Ms: 515.91, p99Ms: 772.56, failures: 0, avgCpuPercent: 2.21, peakRssMb: 64.89 },
        { scenario: 'route_dense', requests: 960, throughputRps: 256.43, p50Ms: 141.76, p95Ms: 514.16, p99Ms: 757.01, failures: 0, avgCpuPercent: 2.13, peakRssMb: 64.94 },
        { scenario: 'body_json', requests: 960, throughputRps: 315.5, p50Ms: 83.41, p95Ms: 348.81, p99Ms: 474.79, failures: 0, avgCpuPercent: 3.03, peakRssMb: 64.39 },
        { scenario: 'body_form', requests: 720, throughputRps: 367.18, p50Ms: 56.16, p95Ms: 261.86, p99Ms: 388.95, failures: 0, avgCpuPercent: 3.53, peakRssMb: 64.61 },
        { scenario: 'body_multipart', requests: 360, throughputRps: 878.15, p50Ms: 10.29, p95Ms: 64.61, p99Ms: 106.7, failures: 0, avgCpuPercent: 13.25, peakRssMb: 78.77 },
        { scenario: 'response_text', requests: 1080, throughputRps: 256.88, p50Ms: 131.92, p95Ms: 516.96, p99Ms: 782.53, failures: 0, avgCpuPercent: 2.09, peakRssMb: 79.92 },
        { scenario: 'response_stream', requests: 360, throughputRps: 473.1, p50Ms: 31.41, p95Ms: 144.74, p99Ms: 227.74, failures: 0, avgCpuPercent: 10.05, peakRssMb: 79.94 },
        { scenario: 'response_file', requests: 600, throughputRps: 465.54, p50Ms: 41.55, p95Ms: 173.26, p99Ms: 253.97, failures: 0, avgCpuPercent: 11.34, peakRssMb: 82.88 },
        { scenario: 'static_file', requests: 720, throughputRps: 391.92, p50Ms: 61.97, p95Ms: 233.62, p99Ms: 336.85, failures: 0, avgCpuPercent: 10.07, peakRssMb: 83.62 },
        { scenario: 'compute_async', requests: 600, throughputRps: 245.03, p50Ms: 141.75, p95Ms: 527.99, p99Ms: 874.2, failures: 0, avgCpuPercent: 2.39, peakRssMb: 83.86 },
        { scenario: 'error_handled', requests: 600, throughputRps: 332.67, p50Ms: 78.0, p95Ms: 305.1, p99Ms: 405.91, failures: 0, avgCpuPercent: 32.48, peakRssMb: 88.83 },
        { scenario: 'error_unhandled', requests: 480, throughputRps: 616.71, p50Ms: 51.34, p95Ms: 58.37, p99Ms: 62.33, failures: 0, avgCpuPercent: 73.2, peakRssMb: 88.88 },
      ],
    },
    {
      name: 'fastapi',
      startupSeconds: 0.3744,
      summary: {
        meanThroughputRps: 281.49,
        meanP95Ms: 485.53,
        failureRatePercent: 0,
      },
      websocket: {
        supported: true,
        skipped: false,
        connections: 12,
        messages: 960,
        throughputMsgsPerSec: 15326.73,
        p95Ms: 0.98,
        failures: 0,
      },
      scenarios: [
        { scenario: 'health', requests: 1200, throughputRps: 240.3, p50Ms: 141.15, p95Ms: 537.37, p99Ms: 836.93, failures: 0, avgCpuPercent: 4.72, peakRssMb: 69.98 },
        { scenario: 'json_simple', requests: 1200, throughputRps: 256.63, p50Ms: 134.02, p95Ms: 508.7, p99Ms: 746.25, failures: 0, avgCpuPercent: 4.18, peakRssMb: 79.12 },
        { scenario: 'json_large', requests: 720, throughputRps: 245.68, p50Ms: 103.66, p95Ms: 527.37, p99Ms: 669.24, failures: 0, avgCpuPercent: 12.82, peakRssMb: 92.56 },
        { scenario: 'di_chain', requests: 1200, throughputRps: 251.83, p50Ms: 141.03, p95Ms: 511.59, p99Ms: 741.64, failures: 0, avgCpuPercent: 7.14, peakRssMb: 98.67 },
        { scenario: 'middleware_stack', requests: 1080, throughputRps: 255.73, p50Ms: 132.33, p95Ms: 507.29, p99Ms: 796.17, failures: 0, avgCpuPercent: 4.19, peakRssMb: 98.67 },
        { scenario: 'route_static', requests: 1080, throughputRps: 256.99, p50Ms: 142.64, p95Ms: 503.49, p99Ms: 772.37, failures: 0, avgCpuPercent: 4.2, peakRssMb: 98.67 },
        { scenario: 'route_params', requests: 1080, throughputRps: 222.36, p50Ms: 154.84, p95Ms: 585.36, p99Ms: 874.49, failures: 0, avgCpuPercent: 4.62, peakRssMb: 98.67 },
        { scenario: 'route_dense', requests: 960, throughputRps: 185.73, p50Ms: 156.65, p95Ms: 851.27, p99Ms: 1315.99, failures: 0, avgCpuPercent: 6.99, peakRssMb: 92.73 },
        { scenario: 'body_json', requests: 960, throughputRps: 280.31, p50Ms: 89.75, p95Ms: 384.43, p99Ms: 529.27, failures: 0, avgCpuPercent: 7.51, peakRssMb: 84.66 },
        { scenario: 'body_form', requests: 720, throughputRps: 343.85, p50Ms: 61.14, p95Ms: 270.57, p99Ms: 417.01, failures: 0, avgCpuPercent: 10.61, peakRssMb: 84.69 },
        { scenario: 'body_multipart', requests: 360, throughputRps: 867.47, p50Ms: 10.65, p95Ms: 54.45, p99Ms: 105.59, failures: 0, avgCpuPercent: 23.05, peakRssMb: 85.31 },
        { scenario: 'response_text', requests: 1080, throughputRps: 208.51, p50Ms: 155.22, p95Ms: 670.22, p99Ms: 1039.84, failures: 0, avgCpuPercent: 5.41, peakRssMb: 85.31 },
        { scenario: 'response_stream', requests: 360, throughputRps: 319.12, p50Ms: 52.16, p95Ms: 173.43, p99Ms: 299.1, failures: 0, avgCpuPercent: 31.53, peakRssMb: 85.33 },
        { scenario: 'response_file', requests: 600, throughputRps: 328.34, p50Ms: 60.72, p95Ms: 236.57, p99Ms: 346.56, failures: 0, avgCpuPercent: 14.19, peakRssMb: 86.64 },
        { scenario: 'static_file', requests: 720, throughputRps: 298.82, p50Ms: 69.12, p95Ms: 291.74, p99Ms: 484.56, failures: 0, avgCpuPercent: 17.99, peakRssMb: 87.86 },
        { scenario: 'compute_async', requests: 600, throughputRps: 126.08, p50Ms: 275.14, p95Ms: 1072.87, p99Ms: 1452.0, failures: 0, avgCpuPercent: 8.43, peakRssMb: 88.3 },
        { scenario: 'error_handled', requests: 600, throughputRps: 162.09, p50Ms: 166.86, p95Ms: 634.28, p99Ms: 975.21, failures: 0, avgCpuPercent: 8.48, peakRssMb: 86.02 },
        { scenario: 'error_unhandled', requests: 480, throughputRps: 216.88, p50Ms: 104.64, p95Ms: 418.54, p99Ms: 542.24, failures: 0, avgCpuPercent: 9.0, peakRssMb: 86.03 },
      ],
    },
    {
      name: 'flask',
      startupSeconds: 0.4457,
      summary: {
        meanThroughputRps: 157.15,
        meanP95Ms: 746.24,
        failureRatePercent: 0,
      },
      websocket: {
        supported: false,
        skipped: true,
        reason: 'websocket_not_supported_in_stack',
      },
      scenarios: [
        { scenario: 'health', requests: 1200, throughputRps: 181.94, p50Ms: 171.87, p95Ms: 780.4, p99Ms: 1274.89, failures: 0, avgCpuPercent: 13.7, peakRssMb: 52.88 },
        { scenario: 'json_simple', requests: 1200, throughputRps: 172.24, p50Ms: 173.43, p95Ms: 863.71, p99Ms: 1427.87, failures: 0, avgCpuPercent: 16.2, peakRssMb: 52.91 },
        { scenario: 'json_large', requests: 720, throughputRps: 200.13, p50Ms: 196.09, p95Ms: 257.47, p99Ms: 286.31, failures: 0, avgCpuPercent: 87.02, peakRssMb: 53.17 },
        { scenario: 'di_chain', requests: 1200, throughputRps: 172.69, p50Ms: 166.01, p95Ms: 905.08, p99Ms: 1399.48, failures: 0, avgCpuPercent: 15.35, peakRssMb: 53.17 },
        { scenario: 'middleware_stack', requests: 1080, throughputRps: 139.83, p50Ms: 230.38, p95Ms: 1014.84, p99Ms: 1681.73, failures: 0, avgCpuPercent: 16.13, peakRssMb: 53.17 },
        { scenario: 'route_static', requests: 1080, throughputRps: 150.06, p50Ms: 163.48, p95Ms: 1186.55, p99Ms: 1884.01, failures: 0, avgCpuPercent: 16.55, peakRssMb: 53.17 },
        { scenario: 'route_params', requests: 1080, throughputRps: 161.28, p50Ms: 176.15, p95Ms: 956.83, p99Ms: 1519.51, failures: 0, avgCpuPercent: 14.89, peakRssMb: 53.17 },
        { scenario: 'route_dense', requests: 960, throughputRps: 130.21, p50Ms: 254.06, p95Ms: 1074.72, p99Ms: 1537.92, failures: 0, avgCpuPercent: 15.45, peakRssMb: 53.17 },
        { scenario: 'body_json', requests: 960, throughputRps: 137.7, p50Ms: 158.95, p95Ms: 873.52, p99Ms: 1376.27, failures: 0, avgCpuPercent: 19.31, peakRssMb: 53.17 },
        { scenario: 'body_form', requests: 720, throughputRps: 118.99, p50Ms: 164.96, p95Ms: 861.48, p99Ms: 1327.82, failures: 0, avgCpuPercent: 17.62, peakRssMb: 53.19 },
        { scenario: 'body_multipart', requests: 360, throughputRps: 232.77, p50Ms: 33.64, p95Ms: 236.57, p99Ms: 449.43, failures: 0, avgCpuPercent: 41.16, peakRssMb: 44.83 },
        { scenario: 'response_text', requests: 1080, throughputRps: 144.17, p50Ms: 179.09, p95Ms: 1148.91, p99Ms: 1949.84, failures: 0, avgCpuPercent: 16.61, peakRssMb: 49.78 },
        { scenario: 'response_stream', requests: 360, throughputRps: 157.31, p50Ms: 134.02, p95Ms: 318.33, p99Ms: 355.83, failures: 0, avgCpuPercent: 67.64, peakRssMb: 50.58 },
        { scenario: 'response_file', requests: 600, throughputRps: 130.12, p50Ms: 149.23, p95Ms: 567.81, p99Ms: 918.17, failures: 0, avgCpuPercent: 20.93, peakRssMb: 51.22 },
        { scenario: 'static_file', requests: 720, throughputRps: 134.23, p50Ms: 148.01, p95Ms: 770.12, p99Ms: 1283.98, failures: 0, avgCpuPercent: 20.08, peakRssMb: 52.12 },
        { scenario: 'compute_async', requests: 600, throughputRps: 140.64, p50Ms: 333.84, p95Ms: 346.99, p99Ms: 348.6, failures: 0, avgCpuPercent: 14.81, peakRssMb: 53.14 },
        { scenario: 'error_handled', requests: 600, throughputRps: 134.95, p50Ms: 188.58, p95Ms: 800.15, p99Ms: 1053.9, failures: 0, avgCpuPercent: 12.69, peakRssMb: 53.56 },
        { scenario: 'error_unhandled', requests: 480, throughputRps: 189.54, p50Ms: 107.6, p95Ms: 468.91, p99Ms: 689.35, failures: 0, avgCpuPercent: 28.37, peakRssMb: 57.75 },
      ],
    },
  ],
}

function titleCase(value: string): string {
  return value.slice(0, 1).toUpperCase() + value.slice(1)
}

function formatScenario(value: string): string {
  return value
    .split('_')
    .map((chunk) => chunk.slice(0, 1).toUpperCase() + chunk.slice(1))
    .join(' ')
}

function formatNumber(value: number): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function BenchmarkPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const scenarioWinners = useMemo(() => {
    const names = benchmarkRun.frameworks[0].scenarios.map((row) => row.scenario)
    return names.map((scenarioName) => {
      const entries = benchmarkRun.frameworks.map((framework) => {
        const row = framework.scenarios.find((item) => item.scenario === scenarioName)
        return {
          framework: framework.name,
          throughputRps: row ? row.throughputRps : 0,
        }
      })

      const winner = entries.reduce((best, current) => {
        if (current.throughputRps > best.throughputRps) {
          return current
        }
        return best
      })

      return {
        scenario: scenarioName,
        winner: winner.framework,
        throughputRps: winner.throughputRps,
      }
    })
  }, [])

  const winnerCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const result of scenarioWinners) {
      counts[result.winner] = (counts[result.winner] || 0) + 1
    }
    return counts
  }, [scenarioWinners])

  const overallLeader = useMemo(() => {
    return [...benchmarkRun.frameworks].sort(
      (left, right) => right.summary.meanThroughputRps - left.summary.meanThroughputRps,
    )[0]
  }, [])

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden">
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />
      <div className="lg:hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      </div>

      <main className="flex-grow pt-16 relative">
        <div
          className={`fixed inset-0 z-[-1] opacity-20 ${isDark ? '' : 'opacity-5'}`}
          style={{
            backgroundImage:
              'linear-gradient(#27272a 1px, transparent 1px), linear-gradient(90deg, #27272a 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
        <div className="fixed inset-0 z-[-1] bg-gradient-to-b from-transparent via-[var(--bg-primary)]/80 to-[var(--bg-primary)]" />

        <section className={`relative pt-12 pb-12 overflow-hidden ${isDark ? 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-aquilia-900/20 via-black to-black' : ''}`}>
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
              <div className={`inline-flex items-center gap-2 mb-5 px-4 py-1.5 rounded-full border text-sm font-medium ${isDark ? 'border-aquilia-500/30 bg-aquilia-500/10 text-aquilia-400' : 'border-aquilia-600/30 bg-aquilia-500/10 text-aquilia-600'}`}>
                <BarChart3 className="w-4 h-4" />
                Benchmark Report
              </div>

              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
                <span className="gradient-text font-mono">Aquilia vs FastAPI vs Flask</span>
              </h1>

              <p className={`text-lg max-w-3xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Comprehensive benchmark from run {benchmarkRun.runId}, covering startup, 18 HTTP scenarios,
                WebSocket throughput, CPU/RSS process sampling, and failure rates.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mt-8">
              <div className={`rounded-2xl border p-5 ${isDark ? 'bg-black/40 border-white/10' : 'bg-white/90 border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Overall Leader</span>
                  <Rocket className="w-4 h-4 text-aquilia-500" />
                </div>
                <div className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{titleCase(overallLeader.name)}</div>
                <div className="text-sm text-aquilia-500 font-semibold mt-1">{formatNumber(overallLeader.summary.meanThroughputRps)} req/s mean throughput</div>
              </div>

              <div className={`rounded-2xl border p-5 ${isDark ? 'bg-black/40 border-white/10' : 'bg-white/90 border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Run Profile</span>
                  <Gauge className="w-4 h-4 text-aquilia-500" />
                </div>
                <div className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  {benchmarkRun.profile.baseRequests} base requests
                </div>
                <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  concurrency {benchmarkRun.profile.concurrency} | warmup {benchmarkRun.profile.warmup}
                </div>
              </div>

              <div className={`rounded-2xl border p-5 ${isDark ? 'bg-black/40 border-white/10' : 'bg-white/90 border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Environment</span>
                  <Server className="w-4 h-4 text-aquilia-500" />
                </div>
                <div className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{benchmarkRun.environment.python}</div>
                <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{benchmarkRun.environment.platform}</div>
                <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{benchmarkRun.environment.cpuCores} CPU cores</div>
              </div>

              <div className={`rounded-2xl border p-5 ${isDark ? 'bg-black/40 border-white/10' : 'bg-white/90 border-gray-200'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>HTTP Winners</span>
                  <Activity className="w-4 h-4 text-aquilia-500" />
                </div>
                <div className={`text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>Aquilia: <span className="font-semibold text-aquilia-500">{winnerCounts.aquilia || 0}</span> scenarios</div>
                <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>FastAPI: {winnerCounts.fastapi || 0} scenarios</div>
                <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Flask: {winnerCounts.flask || 0} scenarios</div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-8 border-y border-[var(--border-color)]/40">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className={`rounded-2xl border overflow-hidden ${isDark ? 'bg-zinc-900/40 border-white/10' : 'bg-white border-gray-200'}`}>
              <div className={`px-6 py-4 border-b ${isDark ? 'border-white/10' : 'border-gray-100'}`}>
                <h2 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Startup and Aggregate Summary</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                    <tr>
                      <th className="px-4 py-3 font-semibold">Framework</th>
                      <th className="px-4 py-3 font-semibold">Startup (s)</th>
                      <th className="px-4 py-3 font-semibold">Mean Throughput (req/s)</th>
                      <th className="px-4 py-3 font-semibold">Mean P95 (ms)</th>
                      <th className="px-4 py-3 font-semibold">Failure Rate (%)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmarkRun.frameworks.map((framework) => (
                      <tr key={framework.name} className={`border-t ${isDark ? 'border-white/10' : 'border-gray-100'}`}>
                        <td className="px-4 py-3 font-semibold text-aquilia-500">{titleCase(framework.name)}</td>
                        <td className="px-4 py-3">{formatNumber(framework.startupSeconds)}</td>
                        <td className="px-4 py-3">{formatNumber(framework.summary.meanThroughputRps)}</td>
                        <td className="px-4 py-3">{formatNumber(framework.summary.meanP95Ms)}</td>
                        <td className="px-4 py-3">{formatNumber(framework.summary.failureRatePercent)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section className="py-8">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <div className="p-1">
                <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>WebSocket Results</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                      <tr>
                        <th className="px-3 py-2 font-semibold">Framework</th>
                        <th className="px-3 py-2 font-semibold">Throughput (msg/s)</th>
                        <th className="px-3 py-2 font-semibold">P95 (ms)</th>
                        <th className="px-3 py-2 font-semibold">Failures</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmarkRun.frameworks.map((framework) => {
                        const ws = framework.websocket
                        return (
                          <tr key={framework.name} className={`border-t ${isDark ? 'border-white/10' : 'border-gray-100'}`}>
                            <td className="px-3 py-2 font-semibold text-aquilia-500">{titleCase(framework.name)}</td>
                            {ws.skipped ? (
                              <>
                                <td className="px-3 py-2" colSpan={3}>Skipped ({ws.reason})</td>
                              </>
                            ) : (
                              <>
                                <td className="px-3 py-2">{formatNumber(ws.throughputMsgsPerSec || 0)}</td>
                                <td className="px-3 py-2">{formatNumber(ws.p95Ms || 0)}</td>
                                <td className="px-3 py-2">{ws.failures || 0}</td>
                              </>
                            )}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="p-1">
                <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Methodology and Interpretation</h3>
                <ul className="space-y-2">
                  {benchmarkRun.methodology.map((line) => (
                    <li key={line} className={`text-sm flex items-start gap-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      <CheckCircle2 className="w-4 h-4 text-aquilia-500 mt-0.5 flex-shrink-0" />
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-5 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5" />
                  <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    This page reflects the latest balanced run in this repository. For confidence intervals, compare across
                    multiple runs in benchmark/results and report median plus spread.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="pb-20">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
            {benchmarkRun.frameworks.map((framework) => (
              <div key={framework.name} className={`rounded-2xl border overflow-hidden ${isDark ? 'bg-zinc-900/30 border-white/10' : 'bg-white border-gray-200'}`}>
                <div className={`px-6 py-4 border-b ${isDark ? 'border-white/10' : 'border-gray-100'}`}>
                  <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {titleCase(framework.name)} Detailed HTTP Scenarios
                  </h3>
                  <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    18 scenario matrix including throughput, latency bands, failure count, and sampled process cost.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm whitespace-nowrap">
                    <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                      <tr>
                        <th className="px-4 py-3 font-semibold">Scenario</th>
                        <th className="px-4 py-3 font-semibold">Requests</th>
                        <th className="px-4 py-3 font-semibold">Throughput</th>
                        <th className="px-4 py-3 font-semibold">P50</th>
                        <th className="px-4 py-3 font-semibold">P95</th>
                        <th className="px-4 py-3 font-semibold">P99</th>
                        <th className="px-4 py-3 font-semibold">Failures</th>
                        <th className="px-4 py-3 font-semibold">Avg CPU %</th>
                        <th className="px-4 py-3 font-semibold">Peak RSS MB</th>
                      </tr>
                    </thead>
                    <tbody>
                      {framework.scenarios.map((row) => (
                        <tr key={`${framework.name}-${row.scenario}`} className={`border-t ${isDark ? 'border-white/10' : 'border-gray-100'}`}>
                          <td className="px-4 py-3 font-medium">{formatScenario(row.scenario)}</td>
                          <td className="px-4 py-3">{row.requests}</td>
                          <td className="px-4 py-3 text-aquilia-500 font-semibold">{formatNumber(row.throughputRps)}</td>
                          <td className="px-4 py-3">{formatNumber(row.p50Ms)}</td>
                          <td className="px-4 py-3">{formatNumber(row.p95Ms)}</td>
                          <td className="px-4 py-3">{formatNumber(row.p99Ms)}</td>
                          <td className="px-4 py-3">{row.failures}</td>
                          <td className="px-4 py-3">{formatNumber(row.avgCpuPercent)}</td>
                          <td className="px-4 py-3">{formatNumber(row.peakRssMb)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="pb-24">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className={`rounded-3xl border p-8 md:p-10 ${isDark ? 'bg-black border-white/10' : 'bg-white border-gray-200 shadow-xl'}`}>
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Artifacts and Reproducibility</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className={`rounded-xl p-4 border ${isDark ? 'bg-zinc-900/40 border-white/10 text-gray-300' : 'bg-gray-50 border-gray-200 text-gray-700'}`}>
                  <div className="font-semibold mb-1">Run directory</div>
                  <div>benchmark/results/{benchmarkRun.runId}</div>
                </div>
                <div className={`rounded-xl p-4 border ${isDark ? 'bg-zinc-900/40 border-white/10 text-gray-300' : 'bg-gray-50 border-gray-200 text-gray-700'}`}>
                  <div className="font-semibold mb-1">Primary files</div>
                  <div>results.json and report.md</div>
                </div>
              </div>

              <div className="mt-6 flex flex-col sm:flex-row gap-3">
                <Link to="/" className={`inline-flex items-center gap-2 px-5 py-3 rounded-xl font-semibold transition-all ${isDark ? 'bg-white text-black hover:scale-[1.02]' : 'bg-aquilia-600 text-white hover:bg-aquilia-700'}`}>
                  Back to Home
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link to="/docs" className={`inline-flex items-center gap-2 px-5 py-3 rounded-xl font-semibold border transition-all ${isDark ? 'border-white/10 text-white hover:bg-white/5' : 'border-gray-300 text-gray-800 hover:bg-gray-50'}`}>
                  Open Documentation
                  <Network className="w-4 h-4" />
                </Link>
                <Link to="/releases" className={`inline-flex items-center gap-2 px-5 py-3 rounded-xl font-semibold border transition-all ${isDark ? 'border-white/10 text-white hover:bg-white/5' : 'border-gray-300 text-gray-800 hover:bg-gray-50'}`}>
                  Release Timeline
                  <Clock3 className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
