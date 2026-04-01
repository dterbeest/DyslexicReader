import { useState, useRef } from 'react'
import FileUpload from './components/FileUpload'
import SettingsPanel from './components/SettingsPanel'
import FontInfo from './components/FontInfo'
import { useSettings } from './hooks/useSettings'
import type { FontFamily } from './hooks/useSettings'
import { convertFile, ConvertError } from './api/convert'

const FONT_FAMILY_CSS: Record<FontFamily, string> = {
  opendyslexic: 'var(--font-od)',
  lexend:       'var(--font-lexend)',
  atkinson:     'var(--font-atkinson)',
}

type Phase = 'idle' | 'converting' | 'done' | 'error'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const { settings, update } = useSettings()
  const [phase, setPhase] = useState<Phase>('idle')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const pdfBlobRef  = useRef<Blob | null>(null)
  const fileNameRef = useRef<string>('')
  const viewUrlRef  = useRef<string | null>(null)

  async function handleConvert() {
    if (!file) return
    fileNameRef.current = file.name.replace(/\.[^.]+$/, '') + '_dyslexic.pdf'
    setPhase('converting')
    setErrorMsg(null)
    try {
      const blob = await convertFile(file, settings)
      pdfBlobRef.current = blob
      setPhase('done')
    } catch (err) {
      const msg = err instanceof ConvertError ? err.message : 'Something went wrong. Please try again.'
      setErrorMsg(msg)
      setPhase('error')
    }
  }

  function handleDownload() {
    if (!pdfBlobRef.current) return
    const url = URL.createObjectURL(pdfBlobRef.current)
    const a = document.createElement('a')
    a.href = url
    a.download = fileNameRef.current
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleViewInBrowser() {
    if (!pdfBlobRef.current) return
    if (viewUrlRef.current) URL.revokeObjectURL(viewUrlRef.current)
    const url = URL.createObjectURL(pdfBlobRef.current)
    viewUrlRef.current = url
    window.open(url, '_blank')
  }

  function handleReset() {
    setFile(null)
    setPhase('idle')
    setErrorMsg(null)
    pdfBlobRef.current = null
    if (viewUrlRef.current) {
      URL.revokeObjectURL(viewUrlRef.current)
      viewUrlRef.current = null
    }
  }

  const locked = phase === 'converting' || phase === 'done'

  return (
    <div className="app">

      <header className="hdr anim-1">
        <div className="wordmark" style={{ fontFamily: FONT_FAMILY_CSS[settings.font_family] }}>DyslexicReader</div>
        <p className="hdr-tagline">
          Convert any image or PDF into a comfortable,<br />
          dyslexia-friendly document in seconds.
        </p>
        <div className="badges">
          <span className="badge">Free</span>
          <span className="badge">Private</span>
          <span className="badge">No account needed</span>
        </div>
      </header>

      <main className="main">

        <div className="card anim-2">

          <div className="card-section">
            <div className="step-label">1 · Upload your file</div>
            <FileUpload onFileSelected={setFile} disabled={locked} />
          </div>

          <div className="card-section">
            <div className="step-label">2 · Customize output</div>
            <SettingsPanel settings={settings} onChange={update} disabled={locked} />
          </div>

          <div className="action-section">

            {phase === 'idle' && (
              <button
                className="btn-convert"
                onClick={handleConvert}
                disabled={!file}
              >
                <span>Convert to PDF</span>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
            )}

            {phase === 'converting' && (
              <div className="state-converting">
                <div className="spinner" aria-label="Converting" />
                <span>Converting your document…</span>
              </div>
            )}

            {phase === 'done' && (
              <div className="state-done">
                <div className="done-check" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <div>
                  <div className="done-title">Your PDF is ready</div>
                  <div className="done-filename">{fileNameRef.current}</div>
                </div>
                <div className="done-btns">
                  <button className="btn-primary" onClick={handleDownload}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Download
                  </button>
                  <button className="btn-secondary" onClick={handleViewInBrowser}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                      <polyline points="15 3 21 3 21 9" />
                      <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                    View in browser
                  </button>
                </div>
                <button className="link-reset" onClick={handleReset}>
                  Convert another file
                </button>
              </div>
            )}

            {phase === 'error' && (
              <div className="state-error">
                <div className="error-icon" aria-hidden="true">
                  <svg width="19" height="19" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <p className="error-msg" role="alert">{errorMsg}</p>
                <button className="btn-retry" onClick={handleReset}>Try again</button>
              </div>
            )}

          </div>
        </div>

        <FontInfo fontFamily={settings.font_family} />

      </main>

      <footer className="footer">
        Files are processed in memory and never stored · No account required
      </footer>

    </div>
  )
}
