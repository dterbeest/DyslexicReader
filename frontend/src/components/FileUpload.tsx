import { useRef, useState } from 'react'
import type { DragEvent, ChangeEvent } from 'react'

const ACCEPTED_TYPES  = ['image/jpeg', 'image/png', 'application/pdf']
const ACCEPTED_EXT    = '.jpg,.jpeg,.png,.pdf'
const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const MAX_PDF_BYTES   = 25 * 1024 * 1024

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function validate(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type))
    return 'Only JPG, PNG, and PDF files are accepted.'
  const limit = file.type === 'application/pdf' ? MAX_PDF_BYTES : MAX_IMAGE_BYTES
  if (file.size > limit)
    return `File is too large. Maximum is ${file.type === 'application/pdf' ? '25 MB' : '10 MB'}.`
  return null
}

interface Props {
  onFileSelected: (file: File | null) => void
  disabled?: boolean
}

export default function FileUpload({ onFileSelected, disabled = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging]         = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError]               = useState<string | null>(null)

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
    e.target.value = ''
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    if (!disabled) setDragging(true)
  }

  function handleDragLeave() { setDragging(false) }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragging(false)
    if (disabled) return
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  function handleClear(e: React.MouseEvent) {
    e.stopPropagation()
    setSelectedFile(null)
    setError(null)
    onFileSelected(null)
  }

  const zoneClass = [
    'upload-zone',
    selectedFile ? 'upload-zone--has-file' : '',
    dragging     ? 'upload-zone--drag'     : '',
    disabled     ? 'upload-zone--disabled' : '',
  ].filter(Boolean).join(' ')

  const isPdf = selectedFile?.type === 'application/pdf'

  return (
    <div>
      <div
        className={zoneClass}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload file — click or drag and drop"
        onClick={() => !disabled && !selectedFile && inputRef.current?.click()}
        onKeyDown={e => {
          if ((e.key === 'Enter' || e.key === ' ') && !disabled && !selectedFile)
            inputRef.current?.click()
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <div className="file-row">
            <div className="file-thumb" aria-hidden="true">
              {isPdf ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="8" y1="13" x2="16" y2="13" />
                  <line x1="8" y1="17" x2="16" y2="17" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
              )}
            </div>
            <div className="file-meta">
              <div className="file-name">{selectedFile.name}</div>
              <div className="file-size">{formatBytes(selectedFile.size)}</div>
            </div>
            {!disabled && (
              <button className="file-clear" onClick={handleClear} aria-label="Remove file">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            )}
          </div>
        ) : (
          <>
            <svg className="upload-icon" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
              aria-hidden="true">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="upload-prompt">
              Drop your file here, or <em>browse</em>
            </p>
            <p className="upload-hint">JPG, PNG or PDF · up to 25 MB</p>
          </>
        )}
      </div>

      {error && <p className="upload-error-msg" role="alert">{error}</p>}

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXT}
        onChange={handleChange}
        disabled={disabled}
        style={{ display: 'none' }}
        aria-hidden="true"
      />
    </div>
  )
}
