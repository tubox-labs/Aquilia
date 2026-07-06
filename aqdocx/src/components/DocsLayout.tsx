import { Outlet } from 'react-router-dom'
import { useState, useRef } from 'react'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'
import { TableOfContents } from './TableOfContents'
import { useTheme } from '../context/ThemeContext'
import { useReactToPrint } from 'react-to-print'
import { Printer } from 'lucide-react'

export function DocsLayout() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const printRef = useRef<HTMLDivElement>(null)

  const handlePrint = useReactToPrint({
    contentRef: printRef,
  })

  return (
    // Lock the viewport — nothing on <body> scrolls
    <div className="h-screen overflow-hidden flex flex-col print:h-auto print:overflow-visible print:block">
      {/* Ambient background — fixed, behind everything */}
      <div className="fixed inset-0 -z-10 pointer-events-none print:hidden">
        <div className={isDark ? 'absolute inset-0 bg-black' : 'absolute inset-0 bg-[#fafafa]'} />
        <div className={`absolute inset-0 ${isDark ? 'bg-gradient-to-br from-aquilia-500/5 via-transparent to-blue-500/5' : ''}`} />
        <div className={`absolute top-0 left-1/4 w-96 h-96 ${isDark ? 'bg-aquilia-500/10' : 'bg-aquilia-500/5'} rounded-full blur-3xl`} />
        <div className={`absolute bottom-0 right-1/4 w-96 h-96 ${isDark ? 'bg-blue-500/10' : 'bg-blue-500/5'} rounded-full blur-3xl`} />
      </div>

      {/* Fixed top navbar */}
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />

      {/*
        Three-column row that fills all remaining height below the navbar.
        pt-16 offsets the fixed navbar (64px).
        overflow-hidden here so only each column scrolls independently.
      */}
      <div className="flex flex-1 overflow-hidden pt-16 print:block print:overflow-visible print:pt-0">

        {/* ── LEFT SIDEBAR ────────────────────────────────────────────
            Full height, scrolls independently via its own overflow-y-auto.
            The Sidebar component itself handles mobile overlay (fixed) and
            desktop (static). We give its wrapper h-full so the inner
            scroll container stretches to the viewport height.
        */}
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

        {/*
          Center + right area: the ONLY scroll container.
          data-scroll-container lets TableOfContents find this element.
        */}
        <div
          className="flex-1 min-w-0 overflow-y-auto print:overflow-visible print:block"
          data-scroll-container=""
        >
          <div className="flex max-w-[80rem] mx-auto print:block print:w-full print:max-w-none">

            {/* Main page content */}
            <main className="flex-1 min-w-0 px-4 sm:px-6 lg:px-10 py-12 print:px-0 print:py-0 print:m-0 print:w-full print:max-w-none print:block">
              <div className="flex justify-end mb-6 print:hidden">
                <button
                  onClick={() => handlePrint()}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                    isDark
                      ? 'border-white/10 text-gray-400 hover:text-aquilia-400 hover:border-aquilia-400/50 bg-white/5 hover:bg-white/10'
                      : 'border-gray-200 text-gray-600 hover:text-aquilia-600 hover:border-aquilia-600/30 bg-gray-50 hover:bg-gray-100'
                  }`}
                  title="Print Article or Save as PDF"
                >
                  <Printer className="w-3.5 h-3.5" />
                  Print Article
                </button>
              </div>
              <div ref={printRef} className="max-w-4xl mx-auto w-full print-content-wrapper">
                <Outlet />

                {/* Footer */}
                <div className={`mt-24 pt-8 border-t ${isDark ? 'border-white/10' : 'border-gray-200'} print:hidden`}>
                  <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                    <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      Last updated: July 2026
                    </p>
                    <a
                      href="https://github.com/axiomchronicles/Aquilia"
                      target="_blank"
                      rel="noopener"
                      className={`flex items-center gap-2 text-sm transition-colors ${isDark ? 'text-gray-500 hover:text-aquilia-400' : 'text-gray-400 hover:text-aquilia-600'}`}
                    >
                      Crafted with ❤️ using Aquilia
                    </a>
                  </div>
                </div>
              </div>
            </main>

            {/* ── RIGHT TOC SIDEBAR ──────────────────────────────────
                sticky top-0 sticks it to the top of the scrolling
                center column, so it never moves as content scrolls.
                Only visible on xl+.
            */}
            <aside className="hidden xl:block w-56 shrink-0 py-12 px-2 print:hidden">
              <div className="sticky top-0">
                <TableOfContents />
              </div>
            </aside>

          </div>
        </div>
      </div>
    </div>
  )
}
