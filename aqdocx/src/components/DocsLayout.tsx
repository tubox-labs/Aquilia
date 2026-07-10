import { Outlet, useLocation } from 'react-router-dom'
import { useState, useRef } from 'react'
import { Navbar } from './Navbar'
import { Sidebar, sections } from './Sidebar'
import { TableOfContents } from './TableOfContents'
import { useTheme } from '../context/ThemeContext'
import { Footer } from './Footer'
import { useReactToPrint } from 'react-to-print'
import { Printer, FileText, BookOpen } from 'lucide-react'
import { SEO } from './SEO'
import { lastUpdatedMap } from '../data/lastUpdatedDates'

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

function getBreadcrumbs(pathname: string): { name: string; url: string }[] {
  const crumbs = [{ name: 'Home', url: 'https://aquilia.tubox.cloud/' }]
  if (pathname === '/docs' || pathname === '/docs/') {
    crumbs.push({ name: 'Documentation', url: 'https://aquilia.tubox.cloud/docs' })
    return crumbs
  }

  const parts = pathname.split('/').filter(Boolean)
  let currentPath = ''
  
  for (let i = 0; i < parts.length; i++) {
    currentPath += '/' + parts[i]
    let label = null
    
    if (currentPath === '/docs') {
      label = 'Documentation'
    } else {
      for (const sec of sections) {
        label = findItemLabel(sec.items, currentPath)
        if (label) break
      }
    }
    
    if (label) {
      crumbs.push({ name: label, url: `https://aquilia.tubox.cloud${currentPath}` })
    }
  }
  return crumbs
}

export function DocsLayout() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isLinkCopied, setIsLinkCopied] = useState(false)
  const printRef = useRef<HTMLDivElement>(null)
  const location = useLocation()

  let pageLabel = 'Documentation'
  for (const sec of sections) {
    const found = findItemLabel(sec.items, location.pathname)
    if (found) {
      pageLabel = found
      break
    }
  }

  const title = `${pageLabel} — Aquilia Documentation`
  const description = `Comprehensive guide and documentation for ${pageLabel} in the Aquilia framework. View API reference, examples, and implementation patterns.`
  const keywords = `Aquilia, ${pageLabel}, Python framework, async, dependency injection, ORM, WebSockets, background tasks`

  const crumbs = getBreadcrumbs(location.pathname)
  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "TechArticle",
        "@id": `https://aquilia.tubox.cloud${location.pathname}#article`,
        "headline": title,
        "description": description,
        "url": `https://aquilia.tubox.cloud${location.pathname}`,
        "inLanguage": "en",
        "author": {
          "@type": "Organization",
          "name": "Aquilia Team"
        }
      },
      {
        "@type": "BreadcrumbList",
        "@id": `https://aquilia.tubox.cloud${location.pathname}#breadcrumbs`,
        "itemListElement": crumbs.map((crumb, index) => ({
          "@type": "ListItem",
          "position": index + 1,
          "name": crumb.name,
          "item": crumb.url
        }))
      }
    ]
  }

  const handlePrint = useReactToPrint({
    contentRef: printRef,
  })

  const [isPrintDropdownOpen, setIsPrintDropdownOpen] = useState(false)

  return (
    // Lock the viewport — nothing on <body> scrolls
    <div className="h-screen overflow-hidden flex flex-col print:h-auto print:overflow-visible print:block">
      <SEO
        title={title}
        description={description}
        keywords={keywords}
        schema={schema}
      />
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
        pt-[var(--navbar-height,64px)] offsets the fixed navbar dynamically.
        overflow-hidden here so only each column scrolls independently.
      */}
      <div className="flex flex-1 overflow-hidden pt-[var(--navbar-height,64px)] print:block print:overflow-visible print:pt-0">

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
                    Print Options
                    <span className="text-[9px] opacity-60">▼</span>
                  </button>

                  {isPrintDropdownOpen && (
                    <>
                      <div 
                        className="fixed inset-0 z-10" 
                        onClick={() => setIsPrintDropdownOpen(false)}
                      />
                      <div className={`absolute right-0 mt-2 w-64 rounded-2xl p-2.5 shadow-[0_10px_40px_rgba(0,0,0,0.15)] dark:shadow-[0_10px_40px_rgba(0,0,0,0.4)] z-20 backdrop-blur-xl transition-all duration-300 overflow-hidden ${
                        isDark 
                          ? 'bg-[#0A0A0A]/95 text-gray-200' 
                          : 'bg-white/95 text-gray-800'
                      }`}>
                        <div className="px-2.5 py-1.5 mb-2 border-b border-gray-100 dark:border-white/5">
                          <span className="text-[10px] font-bold tracking-wider uppercase opacity-40 block">
                            Print Actions
                          </span>
                        </div>
                        <div className="space-y-1">
                          {[
                            {
                              label: 'Print This Page',
                              desc: 'Print only the current section with default formatting.',
                              icon: <FileText className="w-4 h-4 text-blue-500" />,
                              bg: 'hover:bg-aquilia-500/5 dark:hover:bg-white/5',
                              action: () => {
                                setIsPrintDropdownOpen(false)
                                handlePrint()
                              }
                            },
                            {
                              label: 'Print Entire Docs',
                              desc: 'Compile all documentation sections into a single printable handbook.',
                              icon: <BookOpen className="w-4 h-4 text-purple-500" />,
                              bg: 'hover:bg-aquilia-500/5 dark:hover:bg-white/5',
                              action: () => {
                                setIsPrintDropdownOpen(false)
                                window.open('/print-docs', '_blank')
                              }
                            }
                          ].map((item, idx) => (
                            <button
                              key={idx}
                              onClick={item.action}
                              className={`w-full text-left p-2.5 rounded-xl transition-all duration-200 flex gap-3.5 items-start cursor-pointer ${item.bg} group`}
                            >
                              <div className="p-2 rounded-lg bg-gray-100 dark:bg-white/5 transition-transform duration-200 group-hover:scale-105 shrink-0">
                                {item.icon}
                              </div>
                              <div className="space-y-0.5">
                                <span className={`font-semibold text-xs transition-colors group-hover:text-aquilia-400 block ${
                                  isDark ? 'text-white' : 'text-gray-900'
                                }`}>
                                  {item.label}
                                </span>
                                <span className={`text-[10px] leading-relaxed block ${
                                  isDark ? 'text-gray-400' : 'text-gray-500'
                                }`}>
                                  {item.desc}
                                </span>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <div ref={printRef} className="max-w-4xl mx-auto w-full print-content-wrapper">
                <Outlet />

                {/* Document Metadata (Last Updated & Edit on GitHub) */}
                {(() => {
                  const getPageLastUpdated = (path: string) => {
                    const normPath = path.toLowerCase().replace(/\/$/, '')
                    return lastUpdatedMap[normPath] || 'July 10, 2026'
                  }

                  return (
                    <div className={`mt-12 pt-6 border-t ${isDark ? 'border-white/5 text-zinc-500' : 'border-gray-200 text-zinc-400'} text-xs font-mono flex items-center justify-between print:hidden`}>
                      <span>Last updated: {getPageLastUpdated(location.pathname)}</span>
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={() => {
                            navigator.clipboard.writeText(window.location.href)
                            setIsLinkCopied(true)
                            setTimeout(() => setIsLinkCopied(false), 2000)
                          }}
                          className={`hover:underline cursor-pointer transition-colors ${isDark ? 'text-aquilia-400/80 hover:text-aquilia-400' : 'text-aquilia-600/80 hover:text-aquilia-600'}`}
                        >
                          {isLinkCopied ? 'Link copied!' : 'Copy page link'}
                        </button>
                        <span>•</span>
                        <a 
                          href="https://github.com/tubox-labs/Aquilia/issues/new"
                          target="_blank" 
                          rel="noopener noreferrer"
                          className={`hover:underline transition-colors ${isDark ? 'text-aquilia-400/80 hover:text-aquilia-400' : 'text-aquilia-600/80 hover:text-aquilia-600'}`}
                        >
                          Report an issue
                        </a>
                      </div>
                    </div>
                  )
                })()}

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
