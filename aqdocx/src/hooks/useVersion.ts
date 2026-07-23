import { useState, useEffect } from 'react'
import { AQUILIA_VERSION } from '../constants/version'

let cachedVersion = AQUILIA_VERSION
let isFetching = false
const listeners = new Set<(v: string) => void>()

function isGreaterOrEqual(v1: string, v2: string): boolean {
  const p1 = v1.split('.').map(Number)
  const p2 = v2.split('.').map(Number)
  for (let i = 0; i < 3; i++) {
    const num1 = (p1[i] !== undefined && !isNaN(p1[i])) ? p1[i] : 0
    const num2 = (p2[i] !== undefined && !isNaN(p2[i])) ? p2[i] : 0
    if (num1 > num2) return true
    if (num1 < num2) return false
  }
  return true
}

export function useVersion() {
  const [version, setVersion] = useState<string>(cachedVersion)

  useEffect(() => {
    const handleUpdate = (v: string) => setVersion(v)
    listeners.add(handleUpdate)

    if (!isFetching) {
      isFetching = true
      fetch('https://api.github.com/repos/tubox-labs/Aquilia/tags')
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch tags')
          return res.json()
        })
        .then(data => {
          if (Array.isArray(data) && data.length > 0) {
            const stableTag = data.find((tag: any) => {
              const v = tag.name.replace(/^v/, '')
              return !/[ab]|rc|dev|pre/i.test(v)
            })
            if (stableTag) {
              const cleanV = stableTag.name.replace(/^v/, '')
              if (isGreaterOrEqual(cleanV, AQUILIA_VERSION)) {
                cachedVersion = cleanV
                listeners.forEach(l => l(cleanV))
              }
            }
          }
        })
        .catch(() => {
          // Keep AQUILIA_VERSION on fetch error
        })
    }

    return () => {
      listeners.delete(handleUpdate)
    }
  }, [])

  return version
}
