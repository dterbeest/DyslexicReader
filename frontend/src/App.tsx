import { useState, useRef } from 'react'
import FileUpload from './components/FileUpload'
import SettingsPanel from './components/SettingsPanel'
import { useSettings } from './hooks/useSettings'
import { convertFile, ConvertError } from './api/convert'

type Phase = 'idle' | 'converting' | 'done' | 'error'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const { settings, update } = useSettings()
  const [phase, setPhase] = useState<Phase>('idle')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const pdfBlobRef = useRef<Blob | null>(null)
  const fileNameRef = useRef<string>('')

  const converting = phase === 'converting'

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

  function handleReset() {
    setFile(null)
    setPhase('idle')
    setErrorMsg(null)
    pdfBlobRef.current = null
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 bg-white px-4">
      <h1 className="text-4xl font-bold text-gray-900">DyslexicReader</h1>

      {/* Privacy notice — file is never stored */}
      <p className="text-sm text-gray-500 text-center max-w-md">
        Your file is processed entirely in memory and never stored. No data is retained after
        conversion.
      </p>

      <FileUpload onFileSelected={setFile} disabled={converting || phase === 'done'} />
      <SettingsPanel settings={settings} onChange={update} disabled={converting || phase === 'done'} />

      {phase === 'idle' && file && (
        <button
          type="button"
          onClick={handleConvert}
          className="rounded-xl bg-blue-600 px-8 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
        >
          Convert
        </button>
      )}

      {phase === 'converting' && (
        <div className="flex flex-col items-center gap-3">
          <Spinner />
          <p className="text-sm text-gray-600">Converting… this may take up to 30 seconds for large files.</p>
        </div>
      )}

      {phase === 'done' && (
        <div className="flex flex-col items-center gap-3">
          <button
            type="button"
            onClick={handleDownload}
            className="rounded-xl bg-green-600 px-8 py-3 text-white font-medium hover:bg-green-700 transition-colors"
          >
            Download PDF
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="text-sm text-gray-500 underline hover:text-gray-700"
          >
            Convert another file
          </button>
        </div>
      )}

      {phase === 'error' && (
        <div className="flex flex-col items-center gap-3 max-w-sm text-center">
          <p role="alert" className="text-sm text-red-600">{errorMsg}</p>
          <button
            type="button"
            onClick={() => setPhase('idle')}
            className="rounded-xl bg-blue-600 px-8 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
          >
            Try again
          </button>
        </div>
      )}
    </main>
  )
}

function Spinner() {
  return (
    <svg
      className="h-10 w-10 animate-spin text-blue-600"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-label="Loading"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}

export default App
