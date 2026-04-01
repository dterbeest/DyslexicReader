import { useState } from 'react'

export type FontSize = 'small' | 'medium' | 'large'
export type LineSpacing = 'normal' | 'relaxed' | 'double'
export type BgColor = 'white' | 'cream' | 'yellow' | 'blue'

export interface Settings {
  font_size: FontSize
  line_spacing: LineSpacing
  bg_color: BgColor
}

const DEFAULTS: Settings = {
  font_size: 'medium',
  line_spacing: 'relaxed',
  bg_color: 'cream',
}

const STORAGE_KEY = 'dyslexicreader_settings'

function load(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULTS
    return { ...DEFAULTS, ...JSON.parse(raw) }
  } catch {
    return DEFAULTS
  }
}

function save(settings: Settings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch {
    // storage unavailable — silently ignore
  }
}

export function useSettings() {
  const [settings, setSettings] = useState<Settings>(load)

  function update<K extends keyof Settings>(key: K, value: Settings[K]) {
    setSettings((prev) => {
      const next = { ...prev, [key]: value }
      save(next)
      return next
    })
  }

  return { settings, update }
}
