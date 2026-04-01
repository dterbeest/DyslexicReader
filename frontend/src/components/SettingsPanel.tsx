import type { Settings, FontSize, LineSpacing, BgColor, Language } from '../hooks/useSettings'

interface Props {
  settings: Settings
  onChange: <K extends keyof Settings>(key: K, value: Settings[K]) => void
  disabled?: boolean
}

const BG_COLORS: { value: BgColor; label: string; hex: string }[] = [
  { value: 'white',  label: 'White',  hex: '#FFFFFF' },
  { value: 'cream',  label: 'Cream',  hex: '#FFFDD0' },
  { value: 'yellow', label: 'Yellow', hex: '#FAFFA0' },
  { value: 'blue',   label: 'Blue',   hex: '#D0E8FF' },
]

export default function SettingsPanel({ settings, onChange, disabled = false }: Props) {
  return (
    <div className={`settings-grid${disabled ? ' settings-grid--disabled' : ''}`}>

      <div className="setting-row">
        <div className="setting-label">Font size</div>
        <div className="seg" role="radiogroup" aria-label="Font size">
          {(['small', 'medium', 'large'] as FontSize[]).map(v => (
            <div className="seg-item" key={v}>
              <input
                type="radio"
                id={`fs-${v}`}
                name="font_size"
                checked={settings.font_size === v}
                onChange={() => onChange('font_size', v)}
                disabled={disabled}
              />
              <label htmlFor={`fs-${v}`}>
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </label>
            </div>
          ))}
        </div>
      </div>

      <div className="setting-row">
        <div className="setting-label">Line spacing</div>
        <div className="seg" role="radiogroup" aria-label="Line spacing">
          {(['normal', 'relaxed', 'double'] as LineSpacing[]).map(v => (
            <div className="seg-item" key={v}>
              <input
                type="radio"
                id={`ls-${v}`}
                name="line_spacing"
                checked={settings.line_spacing === v}
                onChange={() => onChange('line_spacing', v)}
                disabled={disabled}
              />
              <label htmlFor={`ls-${v}`}>
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </label>
            </div>
          ))}
        </div>
      </div>

      <div className="setting-row">
        <div className="setting-label">Language</div>
        <div className="seg" style={{ maxWidth: '220px' }} role="radiogroup" aria-label="Language">
          {([['eng', 'English'], ['nld', 'Dutch']] as [Language, string][]).map(([v, label]) => (
            <div className="seg-item" key={v}>
              <input
                type="radio"
                id={`lang-${v}`}
                name="language"
                checked={settings.language === v}
                onChange={() => onChange('language', v)}
                disabled={disabled}
              />
              <label htmlFor={`lang-${v}`}>{label}</label>
            </div>
          ))}
        </div>
      </div>

      <div className="setting-row">
        <div className="setting-label">Page background</div>
        <div className="swatches" role="radiogroup" aria-label="Page background color">
          {BG_COLORS.map(({ value, label, hex }) => (
            <div className="swatch" key={value}>
              <input
                type="radio"
                id={`bg-${value}`}
                name="bg_color"
                checked={settings.bg_color === value}
                onChange={() => onChange('bg_color', value)}
                disabled={disabled}
              />
              <label htmlFor={`bg-${value}`}>
                <span className="swatch-dot" style={{ background: hex }} aria-hidden="true" />
                {label}
              </label>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
