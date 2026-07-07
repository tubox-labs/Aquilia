import { Outlet, useLocation } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import { Navbar } from './Navbar'
import { Sidebar, sections } from './Sidebar'
import { TableOfContents } from './TableOfContents'
import { useTheme } from '../context/ThemeContext'
import { Footer } from './Footer'
import { useReactToPrint } from 'react-to-print'
import { Printer, ChevronDown } from 'lucide-react'

// Recursive helper to find page labels
function findItemLabel(items: any[], path: string): string | null {
  for (const item of items) {
    if (item.path.toLowerCase() === path.toLowerCase()) {
      return item.label
    }
    if (item.children) {
      const found = findItemLabel(item.children, path)
      if (found) return found
    }
  }
  return null
}

export function DocsLayout() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const printRef = useRef<HTMLDivElement>(null)
  const location = useLocation()

  useEffect(() => {
    let pageLabel = null
    for (const sec of sections) {
      const found = findItemLabel(sec.items, location.pathname)
      if (found) {
        pageLabel = found
        break
      }
    }
    if (pageLabel) {
      document.title = `${pageLabel} — Aquilia Documentation`
    } else {
      document.title = "Aquilia Documentation"
    }
  }, [location.pathname])

  const handlePrint = useReactToPrint({
    contentRef: printRef,
  })

  const [isPrintDropdownOpen, setIsPrintDropdownOpen] = useState(false)

  const triggerPrint = (printTheme: 'light' | 'dark') => {
    if (printRef.current) {
      printRef.current.setAttribute('data-print-theme', printTheme)
    }
    handlePrint()
    setIsPrintDropdownOpen(false)
  }

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
              <div className="flex justify-end mb-6 print:hidden relative">
                <div className="relative">
                  <button
                    onClick={() => setIsPrintDropdownOpen(!isPrintDropdownOpen)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                      isDark
                        ? 'border-white/10 text-gray-400 hover:text-aquilia-400 hover:border-aquilia-400/50 bg-white/5 hover:bg-white/10'
                        : 'border-gray-200 text-gray-600 hover:text-aquilia-600 hover:border-aquilia-600/30 bg-gray-50 hover:bg-gray-100'
                    }`}
                    title="Print Options"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    Print Article
                    <ChevronDown className="w-3 h-3 opacity-60" />
                  </button>

                  {isPrintDropdownOpen && (
                    <>
                      {/* Click outside overlay */}
                      <div 
                        className="fixed inset-0 z-10" 
                        onClick={() => setIsPrintDropdownOpen(false)} 
                      />
                      {/* Dropdown Menu */}
                      <div className={`absolute right-0 mt-1.5 w-48 rounded-lg shadow-xl border z-20 overflow-hidden ${
                        isDark 
                          ? 'bg-[#0f0f11] border-white/10 text-gray-300' 
                          : 'bg-white border-gray-200 text-gray-700'
                      }`}>
                        <button
                          onClick={() => triggerPrint('light')}
                          className={`w-full text-left px-4 py-2.5 text-xs font-medium transition-colors cursor-pointer ${
                            isDark ? 'hover:bg-white/5 text-gray-300 hover:text-aquilia-400' : 'hover:bg-gray-50 text-gray-700 hover:text-aquilia-600'
                          }`}
                        >
                          Print in Light Theme (Default)
                        </button>
                        <button
                          onClick={() => triggerPrint('dark')}
                          className={`w-full text-left px-4 py-2.5 text-xs font-medium transition-colors cursor-pointer ${
                            isDark ? 'hover:bg-white/5 text-gray-300 hover:text-aquilia-400' : 'hover:bg-gray-50 text-gray-700 hover:text-aquilia-600'
                          }`}
                        >
                          Print in Dark Theme
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <div ref={printRef} className="max-w-4xl mx-auto w-full print-content-wrapper" data-print-theme="light">
                <Outlet />

                {/* Footer */}
                <div className="mt-12 print:hidden">
                  <Footer />
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
