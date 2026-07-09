import { useState, useEffect } from 'react'

let cachedVersion = '1.2.2'
let isFetching = false
const listeners = new Set<(v: string) => void>()

export function useVersion() {
  const [version, setVersion] = useState<string>(cachedVersion)

  useEffect(() => {
    const handleUpdate = (v: string) => setVersion(v)
    listeners.add(handleUpdate)

    if (cachedVersion === '1.2.2' && !isFetching) {
      isFetching = true
      fetch('https://api.github.com/repos/tubox-labs/Aquilia/tags')
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch tags')
          return res.json()
        })
        .then(data => {
          if (Array.isArray(data) && data.length > 0) {
            // Find first tag that is NOT a pre-release (doesn't contain a, b, rc, dev, pre)
            const stableTag = data.find((tag: any) => {
              const v = tag.name.replace(/^v/, '')
              return !/[ab]|rc|dev|pre/i.test(v)
            })
            if (stableTag) {
              const cleanV = stableTag.name.replace(/^v/, '')
              cachedVersion = cleanV
              listeners.forEach(l => l(cleanV))
            }
          }
        })
        .catch(err => {
          console.error('Failed to fetch latest stable version from GitHub:', err)
        })
    }

    return () => {
      listeners.delete(handleUpdate)
    }
  }, [])

  return version
}
