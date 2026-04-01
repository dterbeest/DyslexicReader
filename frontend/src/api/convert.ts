import type { Settings } from '../hooks/useSettings'

const API_BASE = import.meta.env.VITE_API_URL ?? ''
const TIMEOUT_MS = 60_000

export class ConvertError extends Error {
  readonly status?: number
  readonly retryAfterSeconds?: number

  constructor(message: string, status?: number, retryAfterSeconds?: number) {
    super(message)
    this.name = 'ConvertError'
    this.status = status
    this.retryAfterSeconds = retryAfterSeconds
  }
}

function classify(status: number, response: Response): string {
  if (status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After') ?? '3600', 10)
    const minutes = Math.ceil(retryAfter / 60)
    return `You've reached the conversion limit. Please try again in ${minutes} minute${minutes === 1 ? '' : 's'}.`
  }
  if (status === 413) return 'File is too large for the server to process.'
  if (status === 422) return 'The file could not be read. Try a clearer image or a different PDF.'
  return 'Something went wrong. Please try again.'
}

export async function convertFile(file: File, settings: Settings): Promise<Blob> {
  const body = new FormData()
  body.append('file', file)
  body.append('font_size', settings.font_size)
  body.append('line_spacing', settings.line_spacing)
  body.append('bg_color', settings.bg_color)
  body.append('language', settings.language)
  body.append('font_family', settings.font_family)

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  let response: Response
  try {
    response = await fetch(`${API_BASE}/convert`, { method: 'POST', body, signal: controller.signal })
  } catch (err) {
    if ((err as Error).name === 'AbortError') {
      throw new ConvertError('Conversion timed out. Try a smaller file or fewer pages.', 504)
    }
    throw new ConvertError('Conversion timed out. Try a smaller file or fewer pages.')
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    const retryAfter = response.status === 429
      ? parseInt(response.headers.get('Retry-After') ?? '3600', 10)
      : undefined
    throw new ConvertError(classify(response.status, response), response.status, retryAfter)
  }

  return response.blob()
}
