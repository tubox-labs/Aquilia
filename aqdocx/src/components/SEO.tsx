import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { CONSTANTS } from '../data/constants'

interface SEOProps {
  title: string
  description: string
  keywords?: string
  canonical?: string
  ogType?: 'website' | 'article'
  ogImage?: string
  schema?: Record<string, unknown> | Record<string, unknown>[]
}

export function SEO({
  title,
  description,
  keywords,
  canonical,
  ogType = 'website',
  ogImage = CONSTANTS.LOGO_URL,
  schema,
}: SEOProps) {
  const location = useLocation()

  useEffect(() => {
    // 1. Update title
    document.title = title

    // Helper to find or create meta tag
    const updateMeta = (nameOrProperty: string, value: string, isProperty = false) => {
      const selector = isProperty
        ? `meta[property="${nameOrProperty}"]`
        : `meta[name="${nameOrProperty}"]`
      let element = document.querySelector(selector)
      if (!element) {
        element = document.createElement('meta')
        element.setAttribute(isProperty ? 'property' : 'name', nameOrProperty)
        document.head.appendChild(element)
      }
      element.setAttribute('content', value)
    }

    // 2. Set Standard Meta Tags
    updateMeta('description', description)
    if (keywords) {
      updateMeta('keywords', keywords)
    }
    
    // 3. Set Open Graph (Facebook/LinkedIn) Meta Tags
    const canonicalUrl = canonical || `${CONSTANTS.BASE_URL}${location.pathname}`
    updateMeta('og:title', title, true)
    updateMeta('og:description', description, true)
    updateMeta('og:type', ogType, true)
    updateMeta('og:image', ogImage, true)
    updateMeta('og:url', canonicalUrl, true)

    // 4. Set Twitter Card Meta Tags
    updateMeta('twitter:title', title)
    updateMeta('twitter:description', description)
    updateMeta('twitter:image', ogImage)
    updateMeta('twitter:url', canonicalUrl)

    // 5. Update Canonical URL Link Tag
    let canonicalLink = document.querySelector('link[rel="canonical"]')
    if (!canonicalLink) {
      canonicalLink = document.createElement('link')
      canonicalLink.setAttribute('rel', 'canonical')
      document.head.appendChild(canonicalLink)
    }
    canonicalLink.setAttribute('href', canonicalUrl)

    // 6. Inject dynamic JSON-LD Structured Data Schema
    const scriptId = 'dynamic-seo-schema'
    let script = document.getElementById(scriptId) as HTMLScriptElement | null
    if (schema) {
      if (!script) {
        script = document.createElement('script')
        script.id = scriptId
        script.type = 'application/ld+json'
        document.head.appendChild(script)
      }
      script.text = JSON.stringify(schema)
    } else {
      if (script) {
        script.remove()
      }
    }
  }, [title, description, keywords, canonical, ogType, ogImage, schema, location.pathname])

  return null
}
