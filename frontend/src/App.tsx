import { useState } from 'react'
import FileUpload from './components/FileUpload'
import SettingsPanel from './components/SettingsPanel'
import { useSettings } from './hooks/useSettings'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const { settings, update } = useSettings()
  // `converting` will be wired up when the convert endpoint is implemented
  const converting = false

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 bg-white px-4">
      <h1 className="text-4xl font-bold text-gray-900">DyslexicReader</h1>
      <FileUpload onFileSelected={setFile} disabled={converting} />
      <SettingsPanel settings={settings} onChange={update} disabled={converting} />
      {file && !converting && (
        <button
          type="button"
          className="rounded-xl bg-blue-600 px-8 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
        >
          Convert
        </button>
      )}
    </main>
  )
}

export default App
