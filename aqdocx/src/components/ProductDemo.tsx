import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Play, Loader2 } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export function ProductDemo() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [isVideoLoaded, setIsVideoLoaded] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  // Detect user preferences for reduced motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handler = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches)
    }
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  // Handle intersection observation for autoplay/pause behavior
  useEffect(() => {
    const video = videoRef.current
    const container = containerRef.current
    if (!video || !container) return

    const observerOptions = {
      root: null, // viewport
      rootMargin: '0px',
      threshold: 0.25, // Play when 25% visible
    }

    const handleIntersection = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // If user prefers reduced motion, do not autoplay
          if (prefersReducedMotion) return

          // Try playing unmuted first as requested
          video.muted = false
          const playPromise = video.play()
          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                setIsPlaying(true)
              })
              .catch((err) => {
                console.log('Unmuted autoplay prevented, falling back to muted autoplay:', err)
                video.muted = true
                video.play()
                  .then(() => {
                    setIsPlaying(true)
                  })
                  .catch((muteErr) => {
                    console.log('Autoplay fallback failed:', muteErr)
                  })
              })
          }
        } else {
          // Pause immediately when it leaves viewport
          video.pause()
          setIsPlaying(false)
        }
      })
    }

    const observer = new IntersectionObserver(handleIntersection, observerOptions)
    observer.observe(container)

    return () => {
      observer.disconnect()
    }
  }, [prefersReducedMotion])

  // Automatically unmute when user interacts with the page (click, key down, touch start)
  useEffect(() => {
    const handleUserGesture = () => {
      const video = videoRef.current
      if (video && video.muted) {
        video.muted = false
      }
    }

    window.addEventListener('click', handleUserGesture)
    window.addEventListener('keydown', handleUserGesture)
    window.addEventListener('touchstart', handleUserGesture)

    return () => {
      window.removeEventListener('click', handleUserGesture)
      window.removeEventListener('keydown', handleUserGesture)
      window.removeEventListener('touchstart', handleUserGesture)
    }
  }, [])

  const handlePlayPause = () => {
    const video = videoRef.current
    if (!video) return

    if (video.paused) {
      video.muted = false
      video.play()
        .then(() => setIsPlaying(true))
        .catch((err) => console.log('Playback error:', err))
    } else {
      video.pause()
      setIsPlaying(false)
    }
  }

  const handleLoadedData = () => {
    setIsVideoLoaded(true)
    const video = videoRef.current
    if (video) {
      video.muted = false
    }
  }

  return (
    <section
      ref={containerRef}
      className={`py-24 relative overflow-hidden border-b transition-colors duration-300 ${
        isDark
          ? 'bg-gradient-to-b from-black via-zinc-950/20 to-black border-white/5'
          : 'bg-gradient-to-b from-white via-zinc-50/50 to-white border-gray-200'
      }`}
    >
      {/* Premium ambient backdrop glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-aquilia-500/10 blur-[130px] rounded-full pointer-events-none opacity-50 dark:opacity-30" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Headline / Marketing Copy */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          >
            <h2 className="text-aquilia-500 font-bold tracking-wide uppercase text-xs sm:text-sm mb-3">Product Demonstration</h2>
            <h3 className={`text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight mb-6 leading-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
              High-Velocity Python APIs,<br />
              <span className="gradient-text inline-block">Zero Boilerplate</span>
            </h3>
            <p className={`text-base sm:text-lg leading-relaxed max-w-2xl mx-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Watch how Aquilia compiles dependency injection, auto-discovers packages, and handles ASGI traffic. Experience a framework engineered for scale, speed, and modern developer aesthetics.
            </p>
          </motion.div>
        </div>

        {/* Video Showcase Container */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, delay: 0.1, ease: 'easeOut' }}
          className="relative max-w-5xl mx-auto mb-20"
        >
          {/* Video Showcase Player */}
          <div className={`relative aspect-video w-full overflow-hidden rounded-2xl md:rounded-3xl border transition-colors duration-300 ${
            isDark
              ? 'border-white/10 bg-zinc-950 shadow-[0_0_50px_rgba(0,0,0,0.6)]'
              : 'border-gray-200 bg-white shadow-[0_20px_50px_rgba(0,0,0,0.05)]'
          }`}>
            
            {/* Poster/Loading cover */}
            {!isVideoLoaded && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-zinc-950 transition-opacity duration-300">
                <Loader2 className="w-10 h-10 text-aquilia-500 animate-spin mb-4" />
                <span className="text-zinc-500 font-mono text-xs sm:text-sm">Initialising video player...</span>
              </div>
            )}

            {/* Video Element */}
            <video
              ref={videoRef}
              src="https://3aejawfhtwas5inl.public.blob.vercel-storage.com/renders/42ce71a9-b875-46b6-b7c8-0e8a30914c4e.mp4"
              className="w-full h-full object-cover"
              controls
              playsInline
              loop
              onLoadedData={handleLoadedData}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
            />

            {/* Overlay Play Trigger if Autoplay fails or Reduced Motion is on */}
            {isVideoLoaded && !isPlaying && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[2px] z-10 transition-opacity">
                <button
                  onClick={handlePlayPause}
                  className="p-5 rounded-full bg-aquilia-500 text-black hover:scale-110 active:scale-95 transition-all shadow-[0_0_30px_rgba(34,197,94,0.4)] cursor-pointer flex items-center justify-center"
                  aria-label="Play Product Walkthrough"
                >
                  <Play className="w-6 h-6 fill-current translate-x-0.5 text-black" />
                </button>
              </div>
            )}
          </div>
        </motion.div>


      </div>
    </section>
  )
}
