import { useRef, useState } from 'react'
import type { DragEvent, ChangeEvent } from 'react'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'application/pdf']
const ACCEPTED_EXT = '.jpg,.jpeg,.png,.pdf'
const MAX_IMAGE_BYTES = 10 * 1024 * 1024   // 10 MB
const MAX_PDF_BYTES   = 25 * 1024 * 1024   // 25 MB

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function validate(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return 'Only JPG, PNG, and PDF files are accepted.'
  }
  const limit = file.type === 'application/pdf' ? MAX_PDF_BYTES : MAX_IMAGE_BYTES
  if (file.size > limit) {
    const label = file.type === 'application/pdf' ? '25 MB' : '10 MB'
    return `File is too large. Maximum size for this file type is ${label}.`
  }
  return null
}

interface Props {
  onFileSelected: (file: File | null) => void
  disabled?: boolean
}

export default function FileUpload({ onFileSelected, disabled = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  function handleFile(file: File) {
    const err = validate(file)
    if (err) {
      setError(err)
      setSelectedFile(null)
      onFileSelected(null)
    } else {
      setError(null)
      setSelectedFile(file)
      onFileSelected(file)
    }
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    // reset so the same file can be re-selected after clear
    e.target.value = ''
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    if (!disabled) setDragging(true)
  }

  function handleDragLeave() {
    setDragging(false)
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragging(false)
    if (disabled) return
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  function handleClear() {
    setSelectedFile(null)
    setError(null)
    onFileSelected(null)
  }

  const isInteractive = !disabled

  return (
    <div className="w-full max-w-lg">
      {/* Drop zone */}
      <div
        role="button"
        tabIndex={isInteractive ? 0 : -1}
        aria-label="File upload area"
        onClick={() => isInteractive && inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && isInteractive && inputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={[
          'flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition-colors',
          isInteractive ? 'cursor-pointer' : 'cursor-not-allowed opacity-50',
          dragging
            ? 'border-blue-500 bg-blue-50'
            : error
            ? 'border-red-400 bg-red-50'
            : selectedFile
            ? 'border-green-400 bg-green-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50',
        ].join(' ')}
      >
        {selectedFile ? (
          <>
            <FileIcon className="h-10 w-10 text-green-500" />
            <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
            <p className="text-xs text-gray-500">{formatBytes(selectedFile.size)}</p>
          </>
        ) : (
          <>
            <UploadIcon className={`h-10 w-10 ${dragging ? 'text-blue-500' : 'text-gray-400'}`} />
            <div>
              <p className="text-sm font-medium text-gray-700">
                Drag &amp; drop a file here, or{' '}
                <span className="text-blue-600 underline">browse</span>
              </p>
              <p className="mt-1 text-xs text-gray-400">JPG, PNG, PDF — up to 10 MB (25 MB for PDF)</p>
            </div>
          </>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXT}
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />

      {/* Error message */}
      {error && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {error}
        </p>
      )}

      {/* Clear button */}
      {selectedFile && (
        <button
          type="button"
          onClick={handleClear}
          disabled={disabled}
          className="mt-3 text-sm text-gray-500 underline hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Remove file
        </button>
      )}
    </div>
  )
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"
      className={className}>
      <path d="M12 16V4m0 0-4 4m4-4 4 4" />
      <path d="M20 16.5A3.5 3.5 0 0 1 16.5 20h-9A3.5 3.5 0 0 1 4 16.5" />
    </svg>
  )
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"
      className={className}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}
