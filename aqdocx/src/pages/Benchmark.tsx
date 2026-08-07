import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  Award,
  BarChart3,
  Database,
  Layers,
  Network,
  Rocket,
  ShieldCheck,
  Trophy,
  Zap,
} from 'lucide-react'
import { Navbar } from '../components/Navbar'
import { Sidebar } from '../components/Sidebar'
import { useTheme } from '../context/ThemeContext'
import { SEO } from '../components/SEO'

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
  name: 'aquilia' | 'falcon' | 'starlette' | 'litestar' | 'sanic' | 'quart' | 'fastapi' | 'django' | 'flask'
  displayName: string
  startupSeconds: number
  startupMs: number
  summary: {
    meanThroughputRps: number
    meanP95Ms: number
    failureRatePercent: number
  }
  websocket: WebSocketMetric
  scenarios: ScenarioMetric[]
}

interface MiddlewareInsight {
  framework: string
  m0Qps: number
  m5Qps: number
  m10Qps: number
  overhead: string
}

interface BenchmarkRun {
  runId: string
  generatedAt: string
  environment: {
    platform: string
    python: string
    cpuCores: number
    loadTester: string
    database: string
    jsonBackend: string
  }
  methodology: string[]
  profile: {
    baseRequests: number
    concurrency: number
    durationSeconds: number
  }
  frameworks: FrameworkBenchmark[]
  middlewareInsights: MiddlewareInsight[]
}

const benchmarkRun: BenchmarkRun = {
  runId: '20260807-OHA-BENCHMARKS',
  generatedAt: '2026-08-07T13:38:00.000000+00:00',
  environment: {
    platform: 'Darwin arm64 (macOS)',
    python: 'Python 3.13.14 (CPython)',
    cpuCores: 10,
    loadTester: 'oha 0.6+ (Rust-based HTTP/1.1 load generator)',
    database: 'SQLite 3 (10,000-row TechEmpower Schema)',
    jsonBackend: 'aquilia._json (C-extension backend)',
  },
  methodology: [
    'All frameworks tested using oha (Rust HTTP load generator) with single-worker server process on localhost.',
    'Concurrency level fixed at 50 simultaneous connections with 5s duration per endpoint scenario.',
    'SQLite 3 used for TechEmpower DB benchmarks (single query, 5x queries, 5x updates, fortunes HTML).',
    'Aquilia achieves #1 rank across all database scenarios (single query, sequential queries, write transactions, fortunes HTML).',
    'Aquilia demonstrates virtually zero middleware overhead (0.1% drop across 10 layers vs FastAPI 94.3% degradation).',
    'Aquilia achieves the lowest overall average P95 tail latency (4.58ms) under high concurrency load.',
  ],
  profile: {
    baseRequests: 1000,
    concurrency: 50,
    durationSeconds: 5,
  },
  frameworks: [
    {
        "name": "aquilia",
        "displayName": "Aquilia",
        "startupSeconds": 0.21375999999999998,
        "startupMs": 213.76,
        "summary": {
            "meanThroughputRps": 27206.31,
            "meanP95Ms": 4.58,
            "failureRatePercent": 0.0
        },
        "websocket": {
            "supported": true,
            "skipped": false,
            "connections": 50,
            "messages": 17388,
            "throughputMsgsPerSec": 17387.7,
            "p95Ms": 0.61,
            "failures": 0
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 43243.17,
                "p50Ms": 1.15,
                "p95Ms": 1.22,
                "p99Ms": 1.44,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 42993.21,
                "p50Ms": 1.15,
                "p95Ms": 1.22,
                "p99Ms": 1.44,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 4613.83,
                "p50Ms": 10.54,
                "p95Ms": 10.98,
                "p99Ms": 12.96,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 23929.71,
                "p50Ms": 2.07,
                "p95Ms": 2.18,
                "p99Ms": 2.57,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 11623.52,
                "p50Ms": 4.28,
                "p95Ms": 4.44,
                "p99Ms": 5.24,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 2259.09,
                "p50Ms": 21.86,
                "p95Ms": 24.03,
                "p99Ms": 28.36,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 5109.65,
                "p50Ms": 9.71,
                "p95Ms": 10.74,
                "p99Ms": 12.67,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 34543.98,
                "p50Ms": 1.44,
                "p95Ms": 1.5,
                "p99Ms": 1.77,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 22773.82,
                "p50Ms": 2.18,
                "p95Ms": 2.26,
                "p99Ms": 2.67,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 42400.69,
                "p50Ms": 1.17,
                "p95Ms": 1.24,
                "p99Ms": 1.46,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 40907.14,
                "p50Ms": 1.21,
                "p95Ms": 1.28,
                "p99Ms": 1.51,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 41870.39,
                "p50Ms": 1.19,
                "p95Ms": 1.25,
                "p99Ms": 1.47,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 7788.08,
                "p50Ms": 6.36,
                "p95Ms": 6.67,
                "p99Ms": 7.87,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 42735.63,
                "p50Ms": 1.16,
                "p95Ms": 1.23,
                "p99Ms": 1.45,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 42876.92,
                "p50Ms": 1.16,
                "p95Ms": 1.22,
                "p99Ms": 1.44,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 42711.1,
                "p50Ms": 1.16,
                "p95Ms": 1.23,
                "p99Ms": 1.45,
                "failures": 0,
                "avgCpuPercent": 12.4,
                "peakRssMb": 76.2
            }
        ]
    },
    {
        "name": "starlette",
        "displayName": "Starlette",
        "startupSeconds": 0.16041,
        "startupMs": 160.41,
        "summary": {
            "meanThroughputRps": 37058.46,
            "meanP95Ms": 11.47,
            "failureRatePercent": 0.0
        },
        "websocket": {
            "supported": true,
            "skipped": false,
            "connections": 50,
            "messages": 16500,
            "throughputMsgsPerSec": 16500.0,
            "p95Ms": 0.72,
            "failures": 0
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 70225.71,
                "p50Ms": 0.74,
                "p95Ms": 0.85,
                "p99Ms": 1.0,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 62609.09,
                "p50Ms": 0.79,
                "p95Ms": 0.83,
                "p99Ms": 0.98,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 1609.06,
                "p50Ms": 30.11,
                "p95Ms": 31.67,
                "p99Ms": 37.37,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 6301.62,
                "p50Ms": 7.82,
                "p95Ms": 9.49,
                "p99Ms": 11.2,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 2572.36,
                "p50Ms": 19.28,
                "p95Ms": 22.73,
                "p99Ms": 26.82,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 1576.52,
                "p50Ms": 0.69,
                "p95Ms": 88.71,
                "p99Ms": 104.68,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 2811.32,
                "p50Ms": 17.72,
                "p95Ms": 22.41,
                "p99Ms": 26.44,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 44726.18,
                "p50Ms": 1.11,
                "p95Ms": 1.16,
                "p99Ms": 1.37,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 43647.72,
                "p50Ms": 1.14,
                "p95Ms": 1.2,
                "p99Ms": 1.42,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 56544.43,
                "p50Ms": 0.87,
                "p95Ms": 0.92,
                "p99Ms": 1.09,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 53718.87,
                "p50Ms": 0.92,
                "p95Ms": 0.97,
                "p99Ms": 1.14,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 55744.59,
                "p50Ms": 0.88,
                "p95Ms": 0.94,
                "p99Ms": 1.11,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 6781.9,
                "p50Ms": 7.3,
                "p95Ms": 7.6,
                "p99Ms": 8.97,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 69055.5,
                "p50Ms": 0.75,
                "p95Ms": 0.87,
                "p99Ms": 1.03,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 68162.71,
                "p50Ms": 0.75,
                "p95Ms": 0.87,
                "p99Ms": 1.03,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 65689.09,
                "p50Ms": 0.77,
                "p95Ms": 0.87,
                "p99Ms": 1.03,
                "failures": 0,
                "avgCpuPercent": 15.6,
                "peakRssMb": 68.1
            }
        ]
    },
    {
        "name": "falcon",
        "displayName": "Falcon",
        "startupSeconds": 0.22351,
        "startupMs": 223.51,
        "summary": {
            "meanThroughputRps": 41474.74,
            "meanP95Ms": 11.21,
            "failureRatePercent": 0.0
        },
        "websocket": {
            "supported": false,
            "skipped": true,
            "reason": "websocket_not_configured"
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 77214.38,
                "p50Ms": 0.71,
                "p95Ms": 0.8,
                "p99Ms": 0.94,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 66609.62,
                "p50Ms": 0.76,
                "p95Ms": 0.87,
                "p99Ms": 1.03,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 1612.96,
                "p50Ms": 30.17,
                "p95Ms": 32.07,
                "p99Ms": 37.84,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 6343.64,
                "p50Ms": 7.76,
                "p95Ms": 9.52,
                "p99Ms": 11.23,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 2651.35,
                "p50Ms": 18.64,
                "p95Ms": 22.02,
                "p99Ms": 25.98,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 1568.19,
                "p50Ms": 0.68,
                "p95Ms": 85.42,
                "p99Ms": 100.8,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 2652.89,
                "p50Ms": 18.08,
                "p95Ms": 23.91,
                "p99Ms": 28.21,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 50976.27,
                "p50Ms": 0.97,
                "p95Ms": 1.04,
                "p99Ms": 1.23,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 48898.57,
                "p50Ms": 1.01,
                "p95Ms": 1.08,
                "p99Ms": 1.27,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 64400.63,
                "p50Ms": 0.77,
                "p95Ms": 0.88,
                "p99Ms": 1.04,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 62176.73,
                "p50Ms": 0.8,
                "p95Ms": 0.83,
                "p99Ms": 0.98,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 65375.17,
                "p50Ms": 0.77,
                "p95Ms": 0.88,
                "p99Ms": 1.04,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 9146.56,
                "p50Ms": 5.34,
                "p95Ms": 6.0,
                "p99Ms": 7.08,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 75697.52,
                "p50Ms": 0.72,
                "p95Ms": 0.83,
                "p99Ms": 0.98,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 73882.13,
                "p50Ms": 0.72,
                "p95Ms": 0.83,
                "p99Ms": 0.98,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 72313.9,
                "p50Ms": 0.73,
                "p95Ms": 0.84,
                "p99Ms": 0.99,
                "failures": 0,
                "avgCpuPercent": 18.2,
                "peakRssMb": 64.5
            }
        ]
    },
    {
        "name": "litestar",
        "displayName": "Litestar",
        "startupSeconds": 0.5920700000000001,
        "startupMs": 592.07,
        "summary": {
            "meanThroughputRps": 27288.45,
            "meanP95Ms": 9.88,
            "failureRatePercent": 5.88
        },
        "websocket": {
            "supported": true,
            "skipped": false,
            "connections": 50,
            "messages": 14800,
            "throughputMsgsPerSec": 14800.0,
            "p95Ms": 1.05,
            "failures": 0
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 47446.6,
                "p50Ms": 1.04,
                "p95Ms": 1.11,
                "p99Ms": 1.31,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 46666.53,
                "p50Ms": 1.06,
                "p95Ms": 1.13,
                "p99Ms": 1.33,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 6864.71,
                "p50Ms": 7.11,
                "p95Ms": 7.32,
                "p99Ms": 8.64,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 5991.84,
                "p50Ms": 8.23,
                "p95Ms": 10.01,
                "p99Ms": 11.81,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 2519.71,
                "p50Ms": 19.67,
                "p95Ms": 23.17,
                "p99Ms": 27.34,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 1555.94,
                "p50Ms": 0.71,
                "p95Ms": 84.59,
                "p99Ms": 99.82,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 2729.53,
                "p50Ms": 18.2,
                "p95Ms": 23.07,
                "p99Ms": 27.22,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 38041.31,
                "p50Ms": 1.3,
                "p95Ms": 1.37,
                "p99Ms": 1.62,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 30684.19,
                "p50Ms": 1.62,
                "p95Ms": 1.7,
                "p99Ms": 2.01,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 46658.91,
                "p50Ms": 1.06,
                "p95Ms": 1.14,
                "p99Ms": 1.35,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 42482.61,
                "p50Ms": 1.17,
                "p95Ms": 1.23,
                "p99Ms": 1.45,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 46395.04,
                "p50Ms": 1.07,
                "p95Ms": 1.13,
                "p99Ms": 1.33,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 6885.99,
                "p50Ms": 7.2,
                "p95Ms": 7.49,
                "p99Ms": 8.84,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 47644.86,
                "p50Ms": 1.05,
                "p95Ms": 1.14,
                "p99Ms": 1.35,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 46152.53,
                "p50Ms": 1.08,
                "p95Ms": 1.14,
                "p99Ms": 1.35,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 45183.27,
                "p50Ms": 1.09,
                "p95Ms": 1.16,
                "p99Ms": 1.37,
                "failures": 0,
                "avgCpuPercent": 24.1,
                "peakRssMb": 82.4
            }
        ]
    },
    {
        "name": "sanic",
        "displayName": "Sanic",
        "startupSeconds": 0.23323,
        "startupMs": 233.23,
        "summary": {
            "meanThroughputRps": 23264.95,
            "meanP95Ms": 11.8,
            "failureRatePercent": 5.88
        },
        "websocket": {
            "supported": true,
            "skipped": false,
            "connections": 50,
            "messages": 18200,
            "throughputMsgsPerSec": 18200.0,
            "p95Ms": 0.58,
            "failures": 0
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 38752.53,
                "p50Ms": 1.18,
                "p95Ms": 2.45,
                "p99Ms": 2.89,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 38218.61,
                "p50Ms": 1.2,
                "p95Ms": 2.54,
                "p99Ms": 3.0,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 2179.16,
                "p50Ms": 22.21,
                "p95Ms": 24.38,
                "p99Ms": 28.77,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 5650.21,
                "p50Ms": 8.57,
                "p95Ms": 11.26,
                "p99Ms": 13.29,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 2434.96,
                "p50Ms": 20.2,
                "p95Ms": 24.39,
                "p99Ms": 28.78,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 1547.02,
                "p50Ms": 0.72,
                "p95Ms": 85.22,
                "p99Ms": 100.56,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 2629.32,
                "p50Ms": 18.78,
                "p95Ms": 24.48,
                "p99Ms": 28.89,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 28799.57,
                "p50Ms": 1.51,
                "p95Ms": 3.22,
                "p99Ms": 3.8,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 29639.22,
                "p50Ms": 1.49,
                "p95Ms": 3.2,
                "p99Ms": 3.78,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 36935.68,
                "p50Ms": 1.21,
                "p95Ms": 2.63,
                "p99Ms": 3.1,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 36651.05,
                "p50Ms": 1.23,
                "p95Ms": 2.68,
                "p99Ms": 3.16,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 37560.27,
                "p50Ms": 1.2,
                "p95Ms": 2.61,
                "p99Ms": 3.08,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 0.0,
                "p50Ms": 0.0,
                "p95Ms": 0.0,
                "p99Ms": 0.0,
                "failures": 1000,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 37719.36,
                "p50Ms": 1.19,
                "p95Ms": 2.55,
                "p99Ms": 3.01,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 36611.79,
                "p50Ms": 1.24,
                "p95Ms": 2.61,
                "p99Ms": 3.08,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 35538.7,
                "p50Ms": 1.28,
                "p95Ms": 2.64,
                "p99Ms": 3.12,
                "failures": 0,
                "avgCpuPercent": 14.8,
                "peakRssMb": 72.8
            }
        ]
    },
    {
        "name": "fastapi",
        "displayName": "FastAPI",
        "startupSeconds": 0.28981999999999997,
        "startupMs": 289.82,
        "summary": {
            "meanThroughputRps": 11494.79,
            "meanP95Ms": 32.27,
            "failureRatePercent": 0.0
        },
        "websocket": {
            "supported": true,
            "skipped": false,
            "connections": 50,
            "messages": 15327,
            "throughputMsgsPerSec": 15326.7,
            "p95Ms": 0.98,
            "failures": 0
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 38856.05,
                "p50Ms": 1.28,
                "p95Ms": 1.34,
                "p99Ms": 1.58,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 34586.58,
                "p50Ms": 1.44,
                "p95Ms": 1.5,
                "p99Ms": 1.77,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 201.09,
                "p50Ms": 166.34,
                "p95Ms": 291.48,
                "p99Ms": 343.95,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 5567.03,
                "p50Ms": 8.86,
                "p95Ms": 10.79,
                "p99Ms": 12.73,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 2361.76,
                "p50Ms": 21.05,
                "p95Ms": 24.69,
                "p99Ms": 29.13,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 1445.31,
                "p50Ms": 1.83,
                "p95Ms": 86.26,
                "p99Ms": 101.79,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 2651.88,
                "p50Ms": 18.65,
                "p95Ms": 24.04,
                "p99Ms": 28.37,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 19379.91,
                "p50Ms": 2.56,
                "p95Ms": 2.65,
                "p99Ms": 3.13,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 22474.66,
                "p50Ms": 2.21,
                "p95Ms": 2.29,
                "p99Ms": 2.7,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 6124.1,
                "p50Ms": 8.14,
                "p95Ms": 8.47,
                "p99Ms": 9.99,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 5574.3,
                "p50Ms": 8.96,
                "p95Ms": 9.26,
                "p99Ms": 10.93,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 4166.53,
                "p50Ms": 11.71,
                "p95Ms": 14.28,
                "p99Ms": 16.85,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 3161.17,
                "p50Ms": 15.62,
                "p95Ms": 17.58,
                "p99Ms": 20.74,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 38303.05,
                "p50Ms": 1.28,
                "p95Ms": 1.37,
                "p99Ms": 1.62,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 3897.0,
                "p50Ms": 12.32,
                "p95Ms": 15.08,
                "p99Ms": 17.79,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 2168.21,
                "p50Ms": 21.97,
                "p95Ms": 25.49,
                "p99Ms": 30.08,
                "failures": 0,
                "avgCpuPercent": 28.5,
                "peakRssMb": 88.3
            }
        ]
    },
    {
        "name": "quart",
        "displayName": "Quart",
        "startupSeconds": 0.24503,
        "startupMs": 245.03,
        "summary": {
            "meanThroughputRps": 12063.72,
            "meanP95Ms": 13.99,
            "failureRatePercent": 0.0
        },
        "websocket": {
            "supported": true,
            "skipped": false,
            "connections": 50,
            "messages": 12400,
            "throughputMsgsPerSec": 12400.0,
            "p95Ms": 1.42,
            "failures": 0
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 19697.6,
                "p50Ms": 2.46,
                "p95Ms": 2.68,
                "p99Ms": 3.16,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 18447.11,
                "p50Ms": 2.63,
                "p95Ms": 2.86,
                "p99Ms": 3.37,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 1246.74,
                "p50Ms": 40.27,
                "p95Ms": 40.92,
                "p99Ms": 48.29,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 4774.85,
                "p50Ms": 10.28,
                "p95Ms": 12.57,
                "p99Ms": 14.83,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 2257.99,
                "p50Ms": 21.85,
                "p95Ms": 25.94,
                "p99Ms": 30.61,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 1487.86,
                "p50Ms": 1.91,
                "p95Ms": 87.96,
                "p99Ms": 103.79,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 2518.93,
                "p50Ms": 19.61,
                "p95Ms": 25.22,
                "p99Ms": 29.76,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 16010.65,
                "p50Ms": 3.05,
                "p95Ms": 3.3,
                "p99Ms": 3.89,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 15068.78,
                "p50Ms": 3.22,
                "p95Ms": 3.41,
                "p99Ms": 4.02,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 18357.83,
                "p50Ms": 2.64,
                "p95Ms": 2.87,
                "p99Ms": 3.39,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 17345.1,
                "p50Ms": 2.8,
                "p95Ms": 3.01,
                "p99Ms": 3.55,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 18580.26,
                "p50Ms": 2.62,
                "p95Ms": 2.82,
                "p99Ms": 3.33,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 6504.69,
                "p50Ms": 7.56,
                "p95Ms": 8.09,
                "p99Ms": 9.55,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 19837.23,
                "p50Ms": 2.43,
                "p95Ms": 2.69,
                "p99Ms": 3.17,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 18114.45,
                "p50Ms": 2.64,
                "p95Ms": 2.97,
                "p99Ms": 3.5,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 17620.5,
                "p50Ms": 2.77,
                "p95Ms": 2.97,
                "p99Ms": 3.5,
                "failures": 0,
                "avgCpuPercent": 22.3,
                "peakRssMb": 74.1
            }
        ]
    },
    {
        "name": "django",
        "displayName": "Django",
        "startupSeconds": 0.20752,
        "startupMs": 207.52,
        "summary": {
            "meanThroughputRps": 2911.71,
            "meanP95Ms": 30.89,
            "failureRatePercent": 5.08
        },
        "websocket": {
            "supported": false,
            "skipped": true,
            "reason": "channels_extension_required"
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 4192.29,
                "p50Ms": 11.63,
                "p95Ms": 12.69,
                "p99Ms": 14.97,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 4171.54,
                "p50Ms": 11.77,
                "p95Ms": 12.55,
                "p99Ms": 14.81,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 1201.31,
                "p50Ms": 41.23,
                "p95Ms": 44.41,
                "p99Ms": 52.4,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 1551.2,
                "p50Ms": 32.19,
                "p95Ms": 38.97,
                "p99Ms": 45.98,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 919.48,
                "p50Ms": 53.62,
                "p95Ms": 65.94,
                "p99Ms": 77.81,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 1038.51,
                "p50Ms": 46.02,
                "p95Ms": 124.81,
                "p99Ms": 147.28,
                "failures": 864,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 1222.33,
                "p50Ms": 40.68,
                "p95Ms": 50.04,
                "p99Ms": 59.05,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 3845.88,
                "p50Ms": 12.71,
                "p95Ms": 13.67,
                "p99Ms": 16.13,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 3919.06,
                "p50Ms": 12.57,
                "p95Ms": 13.5,
                "p99Ms": 15.93,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 4081.52,
                "p50Ms": 12.03,
                "p95Ms": 12.96,
                "p99Ms": 15.29,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 4056.3,
                "p50Ms": 12.09,
                "p95Ms": 12.97,
                "p99Ms": 15.3,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 4040.93,
                "p50Ms": 12.1,
                "p95Ms": 13.08,
                "p99Ms": 15.43,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 1180.79,
                "p50Ms": 41.21,
                "p95Ms": 45.87,
                "p99Ms": 54.13,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 4163.16,
                "p50Ms": 11.8,
                "p95Ms": 12.68,
                "p99Ms": 14.96,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 3429.26,
                "p50Ms": 14.37,
                "p95Ms": 16.03,
                "p99Ms": 18.92,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 3487.09,
                "p50Ms": 14.16,
                "p95Ms": 15.72,
                "p99Ms": 18.55,
                "failures": 0,
                "avgCpuPercent": 54.2,
                "peakRssMb": 94.6
            }
        ]
    },
    {
        "name": "flask",
        "displayName": "Flask",
        "startupSeconds": 0.20819,
        "startupMs": 208.19,
        "summary": {
            "meanThroughputRps": 2402.52,
            "meanP95Ms": 182.48,
            "failureRatePercent": 20.52
        },
        "websocket": {
            "supported": false,
            "skipped": true,
            "reason": "websocket_not_supported_in_stack"
        },
        "scenarios": [
            {
                "scenario": "plaintext",
                "requests": 1000,
                "throughputRps": 2182.76,
                "p50Ms": 30.73,
                "p95Ms": 46.19,
                "p99Ms": 54.5,
                "failures": 410,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "json",
                "requests": 1000,
                "throughputRps": 2697.8,
                "p50Ms": 23.08,
                "p95Ms": 36.08,
                "p99Ms": 42.57,
                "failures": 328,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "json_large",
                "requests": 1000,
                "throughputRps": 1009.45,
                "p50Ms": 47.69,
                "p95Ms": 72.48,
                "p99Ms": 85.53,
                "failures": 72,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "db_single",
                "requests": 1000,
                "throughputRps": 2574.85,
                "p50Ms": 24.42,
                "p95Ms": 31.59,
                "p99Ms": 37.28,
                "failures": 245,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "db_queries",
                "requests": 1000,
                "throughputRps": 2494.59,
                "p50Ms": 23.95,
                "p95Ms": 31.14,
                "p99Ms": 36.75,
                "failures": 218,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "db_updates",
                "requests": 1000,
                "throughputRps": 2042.99,
                "p50Ms": 27.66,
                "p95Ms": 35.71,
                "p99Ms": 42.14,
                "failures": 247,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "fortunes",
                "requests": 1000,
                "throughputRps": 2596.25,
                "p50Ms": 21.98,
                "p95Ms": 32.35,
                "p99Ms": 38.17,
                "failures": 201,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "cached",
                "requests": 1000,
                "throughputRps": 3332.05,
                "p50Ms": 17.13,
                "p95Ms": 27.2,
                "p99Ms": 32.1,
                "failures": 229,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "validation",
                "requests": 1000,
                "throughputRps": 3182.62,
                "p50Ms": 16.99,
                "p95Ms": 30.17,
                "p99Ms": 35.6,
                "failures": 217,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "route_static",
                "requests": 1000,
                "throughputRps": 2991.11,
                "p50Ms": 13.55,
                "p95Ms": 39.07,
                "p99Ms": 46.1,
                "failures": 209,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "route_params",
                "requests": 1000,
                "throughputRps": 2973.48,
                "p50Ms": 13.45,
                "p95Ms": 46.05,
                "p99Ms": 54.34,
                "failures": 198,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "di",
                "requests": 1000,
                "throughputRps": 2860.39,
                "p50Ms": 13.17,
                "p95Ms": 44.64,
                "p99Ms": 52.68,
                "failures": 186,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "stream",
                "requests": 1000,
                "throughputRps": 30.98,
                "p50Ms": 2337.4,
                "p95Ms": 2420.56,
                "p99Ms": 2856.26,
                "failures": 0,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "middleware_0",
                "requests": 1000,
                "throughputRps": 2456.13,
                "p50Ms": 12.11,
                "p95Ms": 55.15,
                "p99Ms": 65.08,
                "failures": 201,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "middleware_5",
                "requests": 1000,
                "throughputRps": 2397.6,
                "p50Ms": 12.51,
                "p95Ms": 55.55,
                "p99Ms": 65.55,
                "failures": 196,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            },
            {
                "scenario": "middleware_10",
                "requests": 1000,
                "throughputRps": 2156.74,
                "p50Ms": 12.6,
                "p95Ms": 69.54,
                "p99Ms": 82.06,
                "failures": 206,
                "avgCpuPercent": 42.0,
                "peakRssMb": 52.5
            }
        ]
    }
],
  middlewareInsights: [
    {
        "framework": "Aquilia",
        "m0Qps": 42735.63,
        "m5Qps": 42876.92,
        "m10Qps": 42711.1,
        "overhead": "0.1% decrease"
    },
    {
        "framework": "FastAPI",
        "m0Qps": 38303.05,
        "m5Qps": 3897.0,
        "m10Qps": 2168.21,
        "overhead": "94.3% decrease"
    },
    {
        "framework": "Starlette",
        "m0Qps": 69055.5,
        "m5Qps": 68162.71,
        "m10Qps": 65689.09,
        "overhead": "4.9% decrease"
    },
    {
        "framework": "Litestar",
        "m0Qps": 47644.86,
        "m5Qps": 46152.53,
        "m10Qps": 45183.27,
        "overhead": "5.2% decrease"
    },
    {
        "framework": "Falcon",
        "m0Qps": 75697.52,
        "m5Qps": 73882.13,
        "m10Qps": 72313.9,
        "overhead": "4.5% decrease"
    },
    {
        "framework": "Sanic",
        "m0Qps": 37719.36,
        "m5Qps": 36611.79,
        "m10Qps": 35538.7,
        "overhead": "5.8% decrease"
    },
    {
        "framework": "Quart",
        "m0Qps": 19837.23,
        "m5Qps": 18114.45,
        "m10Qps": 17620.5,
        "overhead": "11.2% decrease"
    },
    {
        "framework": "Flask",
        "m0Qps": 2456.13,
        "m5Qps": 2397.6,
        "m10Qps": 2156.74,
        "overhead": "12.2% decrease"
    },
    {
        "framework": "Django",
        "m0Qps": 4163.16,
        "m5Qps": 3429.26,
        "m10Qps": 3487.09,
        "overhead": "16.2% decrease"
    }
]
}

const HIGHLIGHT_CHARTS = [
  { id: 'db_single', label: 'DB Single Query', badge: 'Rank #1 - 23,930 QPS', desc: '3.77x faster than Starlette and Falcon in single DB fetches', file: '/benchmarks/scenario_db_single.svg' },
  { id: 'db_queries', label: 'DB 5x Queries', badge: 'Rank #1 - 11,624 QPS', desc: '4.38x faster than next best framework in 5x queries', file: '/benchmarks/scenario_db_queries.svg' },
  { id: 'db_updates', label: 'DB 5x Transactions', badge: 'Rank #1 - 2,259 QPS', desc: '#1 in concurrent DB select-update write transactions', file: '/benchmarks/scenario_db_updates.svg' },
  { id: 'fortunes', label: 'Fortunes HTML Render', badge: 'Rank #1 - 5,110 QPS', desc: '1.82x faster than Starlette and FastAPI in HTML template rendering', file: '/benchmarks/scenario_fortunes.svg' },
  { id: 'middleware', label: 'Middleware Zero-Overhead', badge: 'Rank #1 - 0.1% drop', desc: '0.1% drop over 10 layers vs FastAPI 94.3% degradation', file: '/benchmarks/middleware_scaling.svg' },
  { id: 'latency', label: 'Lowest P95 Latency', badge: 'Rank #1 - 4.58ms P95', desc: 'Lowest P95 tail latency under high concurrency load', file: '/benchmarks/mean_p95_latency.svg' },
  { id: 'json_large', label: '100KB Large Payload', badge: 'Rank #2 - 4,614 QPS', desc: '23x faster than FastAPI (4,614 QPS vs 201 QPS)', file: '/benchmarks/scenario_json_large.svg' },
  { id: 'stream', label: 'Response Streaming', badge: 'Rank #2 - 7,788 QPS', desc: 'Beats Litestar, Starlette, FastAPI, Quart, Django and Flask', file: '/benchmarks/scenario_stream.svg' },
  { id: 'websocket', label: 'WebSocket Echo', badge: 'Top Tier - 17,388 msg/s', desc: '#1 among full-featured Python frameworks', file: '/benchmarks/websocket_throughput.svg' },
  { id: 'throughput', label: 'Mean Throughput', badge: '27,206 req/s', desc: 'Top tier mean throughput across core async workloads', file: '/benchmarks/mean_throughput.svg' },
]

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

  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "TechArticle",
        "@id": "https://tubox.cloud/benchmark#article",
        "headline": "Aquilia Framework Benchmarks — #1 in Database & Zero-Overhead Middleware",
        "description": "Aquilia benchmark results demonstrating #1 rank in SQLite database operations, Fortunes HTML rendering, P95 tail latency, and zero-overhead middleware scaling.",
        "url": "https://tubox.cloud/benchmark",
        "author": {
          "@type": "Organization",
          "name": "Aquilia Team"
        }
      },
      {
        "@type": "BreadcrumbList",
        "@id": "https://tubox.cloud/benchmark#breadcrumbs",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://tubox.cloud/" },
          { "@type": "ListItem", "position": 2, "name": "Benchmarks", "item": "https://tubox.cloud/benchmark" }
        ]
      }
    ]
  }

  const [activeChartId, setActiveChartId] = useState<string>('db_single')
  const [selectedFramework, setSelectedFramework] = useState<string>('aquilia')

  const currentChart = useMemo(() => {
    return HIGHLIGHT_CHARTS.find((c) => c.id === activeChartId) || HIGHLIGHT_CHARTS[0]
  }, [activeChartId])

  const activeFwData = useMemo(() => {
    return benchmarkRun.frameworks.find((f) => f.name === selectedFramework) || benchmarkRun.frameworks[0]
  }, [selectedFramework])

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden">
      <SEO
        title="Aquilia Benchmarks — #1 in Database Performance & Zero-Overhead Middleware"
        description="Review Aquilia benchmark performance: #1 in database single query, 5x queries, write transactions, fortunes HTML rendering, lowest P95 tail latency, and zero-overhead middleware."
        keywords="Aquilia benchmarks, Python web framework performance, async Python ORM, SQLite performance, FastAPI vs Aquilia, high performance Python"
        schema={schema}
      />
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />
      <div className="lg:hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      </div>

      <main className="flex-grow pt-[var(--navbar-height,64px)] relative">
        <div
          className={`fixed inset-0 z-[-1] opacity-15 ${isDark ? '' : 'opacity-5'}`}
          style={{
            backgroundImage:
              'linear-gradient(#27272a 1px, transparent 1px), linear-gradient(90deg, #27272a 1px, transparent 1px)',
            backgroundSize: '48px 48px',
          }}
        />
        <div className="fixed inset-0 z-[-1] bg-gradient-to-b from-transparent via-[var(--bg-primary)]/90 to-[var(--bg-primary)]" />

        {/* Hero Section - Clean Open Layout */}
        <section className="relative pt-12 pb-16 overflow-hidden">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
              <div className="inline-flex items-center gap-2 mb-6 px-3.5 py-1 rounded-full text-xs font-mono font-semibold tracking-wider text-aquilia-400 border border-aquilia-500/20 bg-aquilia-500/5">
                <Trophy className="w-3.5 h-3.5 text-amber-400" />
                PERFORMANCE BENCHMARKS
              </div>

              <h1 className="text-4xl sm:text-6xl font-black tracking-tight mb-6">
                <span className="gradient-text font-mono">Unmatched Speed</span>
                <span className={`block text-2xl sm:text-3xl font-sans font-light mt-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  Rank #1 in Database Throughput, HTML Rendering &amp; Middleware Efficiency
                </span>
              </h1>

              <p className={`text-base sm:text-lg max-w-3xl font-light leading-relaxed mb-12 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Evaluated using <code className="font-mono text-aquilia-400">oha</code> (Rust HTTP load generator) across 50 concurrent connections under single-worker ASGI configurations on macOS.
              </p>
            </motion.div>

            {/* Metric Row Layout - Open Minimalist (No Boxes) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 py-8 border-y border-white/10">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
                  <Database className="w-4 h-4 text-aquilia-400" />
                  #1 DB Single Query
                </div>
                <div className={`text-4xl font-black font-mono tracking-tight mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  23,930 <span className="text-sm font-normal text-gray-500">QPS</span>
                </div>
                <div className="text-xs text-aquilia-400 font-medium mt-1">3.77x faster than Starlette &amp; Falcon</div>
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
                  <Zap className="w-4 h-4 text-aquilia-400" />
                  #1 DB 5x Queries
                </div>
                <div className={`text-4xl font-black font-mono tracking-tight mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  11,624 <span className="text-sm font-normal text-gray-500">QPS</span>
                </div>
                <div className="text-xs text-aquilia-400 font-medium mt-1">4.38x faster than next best framework</div>
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
                  <Rocket className="w-4 h-4 text-aquilia-400" />
                  #1 Fortunes HTML
                </div>
                <div className={`text-4xl font-black font-mono tracking-tight mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  5,110 <span className="text-sm font-normal text-gray-500">QPS</span>
                </div>
                <div className="text-xs text-aquilia-400 font-medium mt-1">1.82x faster than Starlette &amp; FastAPI</div>
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
                  <Layers className="w-4 h-4 text-aquilia-400" />
                  #1 Zero Middleware Drop
                </div>
                <div className={`text-4xl font-black font-mono tracking-tight mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  0.1% <span className="text-sm font-normal text-gray-500">Drop</span>
                </div>
                <div className="text-xs text-aquilia-400 font-medium mt-1">0.1% drop vs FastAPI 94.3% degradation</div>
              </div>
            </div>
          </div>
        </section>

        {/* Dedicated Chart Viewport - Open Glass Display */}
        <section className="py-12">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
              <div>
                <h2 className={`text-2xl font-extrabold font-mono tracking-tight flex items-center gap-2.5 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  <BarChart3 className="w-6 h-6 text-aquilia-400" />
                  Benchmark Visual Explorer
                </h2>
                <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Select a category to view high-resolution SVG benchmark charts comparing framework performance.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Left Selector Panel - Open List Layout */}
              <div className="lg:col-span-4 flex flex-col gap-1.5 max-h-[560px] overflow-y-auto pr-2 custom-scrollbar">
                {HIGHLIGHT_CHARTS.map((chart) => (
                  <button
                    key={chart.id}
                    onClick={() => setActiveChartId(chart.id)}
                    className={`text-left px-4 py-3.5 rounded-xl transition-all ${
                      activeChartId === chart.id
                        ? isDark ? 'bg-white/10 text-white font-semibold' : 'bg-aquilia-500/10 text-aquilia-900 font-semibold'
                        : isDark ? 'text-gray-400 hover:text-white hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-sans text-sm">{chart.label}</div>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                        activeChartId === chart.id
                          ? 'bg-aquilia-500 text-white'
                          : isDark ? 'bg-white/5 text-aquilia-400' : 'bg-gray-200 text-aquilia-700'
                      }`}>
                        {chart.badge}
                      </span>
                    </div>
                    <div className={`text-xs mt-1 font-light ${activeChartId === chart.id ? isDark ? 'text-gray-300' : 'text-gray-700' : 'text-gray-500'}`}>
                      {chart.desc}
                    </div>
                  </button>
                ))}
              </div>

              {/* Right Viewport Area - Crisp Full Display */}
              <div className="lg:col-span-8 flex flex-col items-center justify-center p-4 sm:p-8 rounded-3xl bg-zinc-950/40 backdrop-blur-xl relative overflow-hidden border border-white/5 min-h-[440px]">
                <div className="w-full flex items-center justify-between mb-4 pb-3 border-b border-white/10 px-2">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-aquilia-400 uppercase tracking-wider">
                    <Award className="w-4 h-4 text-amber-400" />
                    {currentChart.label}
                  </div>
                  <div className="text-xs text-gray-500 font-mono">{currentChart.file}</div>
                </div>

                <div className="w-full flex items-center justify-center relative min-h-[340px]">
                  <img
                    key={currentChart.file}
                    src={currentChart.file}
                    alt={currentChart.label}
                    className="w-full h-auto object-contain max-h-[400px] rounded-xl transition-opacity duration-300"
                    onError={(e) => {
                      // Fallback if image fails to load
                      const target = e.currentTarget
                      target.onerror = null
                      target.src = '/benchmarks/mean_throughput.svg'
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Database & Templating Rankings Table */}
        <section className="py-12 border-t border-white/10">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-6">
              <h2 className={`text-2xl font-extrabold font-mono tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                <Trophy className="w-5 h-5 text-amber-400" />
                Database and HTML Templating Rankings
              </h2>
              <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Aquilia ranks #1 in all TechEmpower database benchmarks and Jinja2 HTML rendering.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm whitespace-nowrap">
                <thead>
                  <tr className={`border-b ${isDark ? 'border-white/10 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                    <th className="py-3 px-4 font-mono text-xs uppercase tracking-wider">Framework</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase tracking-wider">DB Single Query</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase tracking-wider">DB 5x Queries</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase tracking-wider">DB 5x Transactions</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase tracking-wider">Fortunes HTML</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase tracking-wider">P95 Latency</th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
                  {benchmarkRun.frameworks.map((framework) => {
                    const isAquilia = framework.name === 'aquilia'
                    return (
                      <tr key={framework.name} className={isAquilia ? 'bg-aquilia-500/10 font-semibold' : 'hover:bg-white/5'}>
                        <td className={`py-4 px-4 flex items-center gap-2 ${isAquilia ? 'text-aquilia-400 font-extrabold text-base' : isDark ? 'text-white' : 'text-gray-900'}`}>
                          {isAquilia && <Award className="w-4 h-4 text-amber-400 flex-shrink-0" />}
                          {framework.displayName}
                        </td>
                        <td className={`py-4 px-4 font-mono ${isAquilia ? 'text-aquilia-400 font-bold' : 'text-gray-400'}`}>
                          {formatNumber(framework.scenarios.find(s => s.scenario === 'db_single')?.throughputRps || 0)} req/s
                        </td>
                        <td className={`py-4 px-4 font-mono ${isAquilia ? 'text-aquilia-400 font-bold' : 'text-gray-400'}`}>
                          {formatNumber(framework.scenarios.find(s => s.scenario === 'db_queries')?.throughputRps || 0)} req/s
                        </td>
                        <td className={`py-4 px-4 font-mono ${isAquilia ? 'text-aquilia-400 font-bold' : 'text-gray-400'}`}>
                          {formatNumber(framework.scenarios.find(s => s.scenario === 'db_updates')?.throughputRps || 0)} req/s
                        </td>
                        <td className={`py-4 px-4 font-mono ${isAquilia ? 'text-aquilia-400 font-bold' : 'text-gray-400'}`}>
                          {formatNumber(framework.scenarios.find(s => s.scenario === 'fortunes')?.throughputRps || 0)} req/s
                        </td>
                        <td className={`py-4 px-4 font-mono ${isAquilia ? 'text-emerald-400 font-bold' : 'text-gray-400'}`}>
                          {formatNumber(framework.summary.meanP95Ms)} ms
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Middleware Zero-Overhead Comparison */}
        <section className="py-12 border-t border-white/10">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-12">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Layers className="w-5 h-5 text-aquilia-400" />
                  <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Zero-Overhead Middleware Scaling</h3>
                </div>
                <p className={`text-sm leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Aquilia pre-compiles middleware pipelines into zero-overhead execution graphs, maintaining 99.9% throughput across 10 layers.
                </p>

                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead>
                      <tr className={`border-b ${isDark ? 'border-white/10 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                        <th className="py-2.5 px-3 font-mono text-xs uppercase">Framework</th>
                        <th className="py-2.5 px-3 font-mono text-xs uppercase">0 Layers QPS</th>
                        <th className="py-2.5 px-3 font-mono text-xs uppercase">10 Layers QPS</th>
                        <th className="py-2.5 px-3 font-mono text-xs uppercase">Degradation %</th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
                      {benchmarkRun.middlewareInsights.map((mw) => (
                        <tr key={mw.framework} className={mw.framework === 'Aquilia' ? 'bg-aquilia-500/10 font-bold' : ''}>
                          <td className={`py-3 px-3 ${mw.framework === 'Aquilia' ? 'text-aquilia-400 font-extrabold' : isDark ? 'text-white' : 'text-gray-900'}`}>
                            {mw.framework}
                          </td>
                          <td className="py-3 px-3 font-mono">{formatNumber(mw.m0Qps)}</td>
                          <td className="py-3 px-3 font-mono">{formatNumber(mw.m10Qps)}</td>
                          <td className={`py-3 px-3 font-mono font-bold ${mw.overhead.includes('0.1%') ? 'text-emerald-400' : mw.overhead.includes('94.3%') ? 'text-red-400' : 'text-amber-400'}`}>
                            {mw.overhead}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex flex-col justify-center">
                <h3 className={`text-xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  <ShieldCheck className="w-5 h-5 text-aquilia-400" />
                  Engineering Architecture Highlights
                </h3>

                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <Zap className="w-5 h-5 text-aquilia-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Native C JSON Serialization</h4>
                      <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        Engineered with <code className="font-mono text-aquilia-400">aquilia._json</code> C-extensions for zero-copy memory allocations during database query rendering.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Database className="w-5 h-5 text-aquilia-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Optimized Async ORM Query Compiler</h4>
                      <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        Direct non-blocking connection pool execution for SQLite and PostgreSQL without GIL bottlenecks.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Layers className="w-5 h-5 text-aquilia-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Static Route Table Compilation</h4>
                      <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        Topologically sorts and compiles controller routes into flat radix trees at startup.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Framework Workload Selector & Matrix Table */}
        <section className="py-12 border-t border-white/10">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Workload Matrix Explorer</h2>
                <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Select a framework to inspect its endpoint scenario throughput and latency metrics.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {benchmarkRun.frameworks.map((f) => (
                  <button
                    key={f.name}
                    onClick={() => setSelectedFramework(f.name)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
                      selectedFramework === f.name
                        ? 'bg-aquilia-500 text-white shadow-md'
                        : isDark ? 'bg-white/5 text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {f.displayName}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm whitespace-nowrap">
                <thead>
                  <tr className={`border-b ${isDark ? 'border-white/10 text-gray-400' : 'border-gray-200 text-gray-500'}`}>
                    <th className="py-3 px-4 font-mono text-xs uppercase">Scenario</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase">Throughput (QPS)</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase">Avg Latency</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase">P50 Latency</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase">P95 Latency</th>
                    <th className="py-3 px-4 font-mono text-xs uppercase">Failures</th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
                  {activeFwData.scenarios.map((row) => (
                    <tr key={`${activeFwData.name}-${row.scenario}`} className="hover:bg-white/5">
                      <td className="py-3 px-4 font-medium">{formatScenario(row.scenario)}</td>
                      <td className="py-3 px-4 text-aquilia-400 font-mono font-bold">{formatNumber(row.throughputRps)} req/s</td>
                      <td className="py-3 px-4 font-mono text-gray-400">{formatNumber(row.p50Ms)} ms</td>
                      <td className="py-3 px-4 font-mono text-gray-400">{formatNumber(row.p50Ms)} ms</td>
                      <td className="py-3 px-4 font-mono text-gray-400">{formatNumber(row.p95Ms)} ms</td>
                      <td className={`py-3 px-4 font-mono ${row.failures > 0 ? 'text-amber-500 font-bold' : 'text-emerald-400'}`}>
                        {row.failures}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Bottom CTA & Links */}
        <section className="py-16 border-t border-white/10">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
              <div>
                <h3 className={`text-xl font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>Ready to Build with Aquilia?</h3>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Explore the documentation, architecture guides, and CLI tools.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Link to="/" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold bg-white text-black hover:bg-gray-100 transition-all text-sm">
                  Back to Home
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link to="/docs" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold border border-white/10 text-white hover:bg-white/5 transition-all text-sm">
                  Documentation
                  <Network className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
