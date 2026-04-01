import type { Settings, FontSize, LineSpacing, BgColor } from '../hooks/useSettings'

interface Props {
  settings: Settings
  onChange: <K extends keyof Settings>(key: K, value: Settings[K]) => void
  disabled?: boolean
}

const BG_META: { value: BgColor; label: string; hex: string; ring: string }[] = [
  { value: 'white',  label: 'White',  hex: '#FFFFFF', ring: 'ring-gray-300' },
  { value: 'cream',  label: 'Cream',  hex: '#FFFDD0', ring: 'ring-yellow-300' },
  { value: 'yellow', label: 'Yellow', hex: '#FAFFA0', ring: 'ring-yellow-400' },
  { value: 'blue',   label: 'Blue',   hex: '#D0E8FF', ring: 'ring-blue-400' },
]

export default function SettingsPanel({ settings, onChange, disabled = false }: Props) {
  return (
    <div className="w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-5 shadow-sm space-y-5">
      <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Output settings</h2>

      {/* Font size */}
      <fieldset disabled={disabled}>
        <legend className="mb-2 text-sm font-medium text-gray-700">Font size</legend>
        <SegmentedControl<FontSize>
          name="font_size"
          options={[
            { value: 'small',  label: 'Small' },
            { value: 'medium', label: 'Medium' },
            { value: 'large',  label: 'Large' },
          ]}
          value={settings.font_size}
          onChange={(v) => onChange('font_size', v)}
        />
      </fieldset>

      {/* Line spacing */}
      <fieldset disabled={disabled}>
        <legend className="mb-2 text-sm font-medium text-gray-700">Line spacing</legend>
        <SegmentedControl<LineSpacing>
          name="line_spacing"
          options={[
            { value: 'normal',  label: 'Normal' },
            { value: 'relaxed', label: 'Relaxed' },
            { value: 'double',  label: 'Double' },
          ]}
          value={settings.line_spacing}
          onChange={(v) => onChange('line_spacing', v)}
        />
      </fieldset>

      {/* Background color */}
      <fieldset disabled={disabled}>
        <legend className="mb-2 text-sm font-medium text-gray-700">Page background</legend>
        <div className="flex gap-3 flex-wrap">
          {BG_META.map(({ value, label, hex, ring }) => {
            const selected = settings.bg_color === value
            return (
              <label key={value} className="flex flex-col items-center gap-1 cursor-pointer">
                <input
                  type="radio"
                  name="bg_color"
                  value={value}
                  checked={selected}
                  onChange={() => onChange('bg_color', value)}
                  className="sr-only"
                />
                <span
                  aria-hidden
                  className={[
                    'h-8 w-8 rounded-full border border-gray-300 ring-offset-2 transition-shadow',
                    selected ? `ring-2 ${ring}` : '',
                    disabled ? 'opacity-50 cursor-not-allowed' : '',
                  ].join(' ')}
                  style={{ backgroundColor: hex }}
                />
                <span className="text-xs text-gray-600">{label}</span>
              </label>
            )
          })}
        </div>

        {/* Live preview strip */}
        <div
          className="mt-3 h-6 w-full rounded-lg border border-gray-200 transition-colors"
          style={{ backgroundColor: BG_META.find((b) => b.value === settings.bg_color)?.hex }}
          aria-label={`Preview of ${settings.bg_color} background`}
        />
      </fieldset>
    </div>
  )
}

// ---- Segmented control ----

interface SegOption<T extends string> {
  value: T
  label: string
}

interface SegProps<T extends string> {
  name: string
  options: SegOption<T>[]
  value: T
  onChange: (v: T) => void
}

function SegmentedControl<T extends string>({ name, options, value, onChange }: SegProps<T>) {
  return (
    <div className="flex rounded-lg border border-gray-200 overflow-hidden">
      {options.map((opt, i) => {
        const selected = opt.value === value
        return (
          <label
            key={opt.value}
            className={[
              'flex-1 text-center',
              i > 0 ? 'border-l border-gray-200' : '',
            ].join(' ')}
          >
            <input
              type="radio"
              name={name}
              value={opt.value}
              checked={selected}
              onChange={() => onChange(opt.value)}
              className="sr-only"
            />
            <span
              className={[
                'block py-1.5 text-sm font-medium cursor-pointer select-none transition-colors',
                selected
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50',
                'fieldset:disabled:cursor-not-allowed fieldset:disabled:opacity-50',
              ].join(' ')}
            >
              {opt.label}
            </span>
          </label>
        )
      })}
    </div>
  )
}
