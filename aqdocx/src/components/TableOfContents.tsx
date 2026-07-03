import { useEffect, useRef, useState, useLayoutEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { AlignLeft } from 'lucide-react'

interface Heading {
  id: string
  text: string
  level: number
}

export function TableOfContents() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const location = useLocation()

  const [headings, setHeadings] = useState<Heading[]>([])
  const [activeId, setActiveId] = useState<string>('')
  const [scrollDir, setScrollDir] = useState<'down' | 'up' | 'stable'>('stable')
  const lastScrollTop = useRef(0)
  const scrollTimeoutRef = useRef<number | null>(null)
  const [arrowY, setArrowY] = useState(0)
  const [arrowVisible, setArrowVisible] = useState(false)

  const observerRef = useRef<IntersectionObserver | null>(null)
  const rowRefs = useRef<Map<string, HTMLAnchorElement>>(new Map())
  const navRef = useRef<HTMLDivElement>(null)

  // ── Track scrolling on the scroll container ──────────────────────
  useEffect(() => {
    const container = document.querySelector('[data-scroll-container]')
    if (!container) return

    const handleScroll = () => {
      const currentScrollTop = container.scrollTop
      const diff = currentScrollTop - lastScrollTop.current

      // Threshold to avoid jitter
      if (Math.abs(diff) > 2) {
        setScrollDir(diff > 0 ? 'down' : 'up')
      }

      lastScrollTop.current = currentScrollTop

      if (scrollTimeoutRef.current) {
        window.clearTimeout(scrollTimeoutRef.current)
      }

      scrollTimeoutRef.current = window.setTimeout(() => {
        setScrollDir('stable')
      }, 150)
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      container.removeEventListener('scroll', handleScroll)
      if (scrollTimeoutRef.current) {
        window.clearTimeout(scrollTimeoutRef.current)
      }
    }
  }, [headings])

  // ── Extract headings ──────────────────────────────────────────────
  useEffect(() => {
    rowRefs.current.clear()
    const extract = () => {
      const els = Array.from(document.querySelectorAll('h1, h2, h3')) as HTMLElement[]
      const extracted: Heading[] = els
        .filter((el) => el.textContent?.trim())
        .map((el) => {
          if (!el.id) {
            el.id = el.textContent!.trim().toLowerCase()
              .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
          }
          return { id: el.id, text: el.textContent!.trim(), level: parseInt(el.tagName[1]) }
        })
        .filter((h) => h.level >= 2 && h.level <= 3)
        .slice(0, 22)
      setHeadings(extracted)
      setActiveId('')
      setArrowVisible(false)
    }
    const t = setTimeout(extract, 160)
    return () => clearTimeout(t)
  }, [location.pathname])

  // ── IntersectionObserver ──────────────────────────────────────────
  useEffect(() => {
    if (headings.length === 0) return
    observerRef.current?.disconnect()
    const scrollRoot = document.querySelector('[data-scroll-container]') ?? null
    const visible = new Set<string>()
    const cb: IntersectionObserverCallback = (entries) => {
      entries.forEach((e) => (e.isIntersecting ? visible.add(e.target.id) : visible.delete(e.target.id)))
      for (const h of headings) {
        if (visible.has(h.id)) { setActiveId(h.id); return }
      }
    }
    observerRef.current = new IntersectionObserver(cb, {
      root: scrollRoot, rootMargin: '-64px 0px -50% 0px', threshold: 0,
    })
    headings.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (el) observerRef.current!.observe(el)
    })
    return () => observerRef.current?.disconnect()
  }, [headings])

  // ── Slide arrow to active item ────────────────────────────────────
  useLayoutEffect(() => {
    if (!activeId || !navRef.current) return
    const anchor = rowRefs.current.get(activeId)
    if (!anchor) return
    const navRect = navRef.current.getBoundingClientRect()
    const aRect = anchor.getBoundingClientRect()
    setArrowY(aRect.top - navRect.top + aRect.height / 2)
    setArrowVisible(true)
  }, [activeId, headings])

  // ── Scroll ────────────────────────────────────────────────────────
  const scrollTo = (id: string, e: React.MouseEvent) => {
    e.preventDefault()
    const el = document.getElementById(id)
    if (!el) return
    const c = document.querySelector('[data-scroll-container]')
    if (c) {
      const top = el.getBoundingClientRect().top - c.getBoundingClientRect().top + c.scrollTop - 80
      c.scrollTo({ top, behavior: 'smooth' })
    } else {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  if (headings.length === 0) return null

  // Determine rotation based on scroll state
  let rotation = 0 // stable: points right (▶)
  if (scrollDir === 'down') rotation = 90  // points down (▼)
  if (scrollDir === 'up') rotation = -90   // points up (▲)

  return (
    <div className="pt-2 pb-12 select-none w-full">

      {/* Header */}
      <h3 className={`inline-flex items-center gap-1.5 text-xs mb-3 font-medium ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
        <AlignLeft className="w-3.5 h-3.5 shrink-0" />
        On this page
      </h3>

      {/* Nav */}
      <div className="relative py-1" ref={navRef}>

        {/* Sliding dynamic rotating arrow */}
        <div
          aria-hidden
          className="pointer-events-none absolute"
          style={{
            left: 0,
            top: arrowY,
            transform: 'translateY(-50%)',
            opacity: arrowVisible ? 1 : 0,
            transition: 'top 280ms cubic-bezier(0.34,1.4,0.64,1), opacity 150ms ease',
          }}
        >
          <svg
            width="16"
            height="12"
            viewBox="0 0 16 12"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{
              transform: `rotate(${rotation}deg)`,
              transition: 'transform 220ms cubic-bezier(0.34, 1.4, 0.64, 1)',
              transformOrigin: '8px 6px',
            }}
          >
            {/* Horizontal shaft */}
            <rect
              x="0" y="5"
              width="10" height="2"
              rx="1"
              fill={isDark ? '#22c55e' : '#16a34a'}
            />
            {/* Arrowhead pointing right */}
            <polygon
              points="8,1 15,6 8,11"
              fill={isDark ? '#22c55e' : '#16a34a'}
            />
          </svg>
        </div>

        {/* Items */}
        <div className="flex flex-col">
          {headings.map(({ id, text, level }) => {
            const isActive = activeId === id
            const isH3 = level === 3
            return (
              <a
                key={id}
                href={`#${id}`}
                ref={(el) => {
                  if (el) rowRefs.current.set(id, el)
                  else rowRefs.current.delete(id)
                }}
                onClick={(e) => scrollTo(id, e)}
                className={[
                  'block py-1.5 truncate transition-colors duration-150',
                  isH3 ? 'text-[11px] pl-9' : 'text-[12px] pl-7',
                  isActive
                    ? isDark ? 'text-green-400 font-semibold' : 'text-green-600 font-semibold'
                    : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-400 hover:text-gray-700',
                ].join(' ')}
              >
                {text}
              </a>
            )
          })}
        </div>
      </div>
    </div>
  )
}
