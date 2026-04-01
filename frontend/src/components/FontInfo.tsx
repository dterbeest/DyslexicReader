import { useState } from 'react'
import type { FontFamily } from '../hooks/useSettings'

interface Props {
  fontFamily: FontFamily
}

interface FontData {
  name: string
  tagline: string
  cssFamily: string
  bodyText: string
  features: string[]
  credit: { designer: string; url: string; urlLabel: string }
}

const FONT_DATA: Record<FontFamily, FontData> = {
  opendyslexic: {
    name: 'OpenDyslexic',
    tagline: 'Designed to reduce common reading difficulties',
    cssFamily: 'var(--font-od)',
    bodyText:
      'OpenDyslexic is a free, open-source typeface created by Abbie Gonzalez, designed to reduce some of the common reading difficulties associated with dyslexia. Each character has a unique shape and a heavy weighted bottom that anchors letters to the baseline — preventing them from visually rotating or flipping.',
    features: [
      'Heavy bottoms anchor letters to the baseline',
      'Unique shapes reduce b/d and p/q confusion',
      'Wider spacing aids word recognition',
      'Free and open source — SIL Open Font License',
    ],
    credit: {
      designer: 'Abbie Gonzalez',
      url: 'https://opendyslexic.org',
      urlLabel: 'opendyslexic.org',
    },
  },
  lexend: {
    name: 'Lexend',
    tagline: 'Designed to improve reading proficiency and reduce visual stress',
    cssFamily: 'var(--font-lexend)',
    bodyText:
      'Lexend is a variable font family designed by Thomas Jockin, based on the research of educational therapist Bonnie Shaver-Troup. It uses customised letter-spacing and shaping to reduce visual stress and crowding — making it easier to decode words quickly and accurately.',
    features: [
      'Reduced visual crowding between letters',
      'Research-based letter spacing and shaping',
      'Clean geometric forms aid rapid decoding',
      'Free via Google Fonts',
    ],
    credit: {
      designer: 'Thomas Jockin',
      url: 'https://www.lexend.com',
      urlLabel: 'lexend.com',
    },
  },
  atkinson: {
    name: 'Atkinson Hyperlegible',
    tagline: 'Designed for maximum legibility for low-vision readers',
    cssFamily: 'var(--font-atkinson)',
    bodyText:
      'Atkinson Hyperlegible was created by the Braille Institute of America to improve legibility for readers with low vision. It focuses on exaggerating the distinguishing features of letterforms, making commonly confused characters unmistakably different from one another.',
    features: [
      'Exaggerated letterform distinctions reduce misreading',
      'High contrast strokes improve clarity',
      'Optimised for small sizes and low vision',
      'Free and open source',
    ],
    credit: {
      designer: 'Braille Institute of America',
      url: 'https://www.brailleinstitute.org/freefont',
      urlLabel: 'brailleinstitute.org',
    },
  },
}

export default function FontInfo({ fontFamily }: Props) {
  const [open, setOpen] = useState(false)
  const data = FONT_DATA[fontFamily]

  return (
    <section className="font-info anim-3" aria-label={`About ${data.name}`}>

      <button
        className="font-info-toggle"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <div className="font-info-mark" style={{ fontFamily: data.cssFamily }} aria-hidden="true">Aa</div>
        <div className="font-info-toggle-label">
          <div className="font-info-toggle-title">About {data.name}</div>
          <div className="font-info-toggle-sub">The typeface behind every converted document</div>
        </div>
        <svg
          className={`font-info-chevron${open ? ' font-info-chevron--open' : ''}`}
          width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="font-info-body">

          <div className="font-info-header">
            <div>
              <h2 className="font-info-title">{data.name}</h2>
              <p className="font-info-sub">{data.tagline}</p>
            </div>
          </div>

          <div className="font-specimen">
            <div className="specimen-label">Font specimen</div>
            <p className="specimen-text" style={{ fontFamily: data.cssFamily }}>
              Reading should feel easy. Every letter has a unique shape
              so your eye never confuses one for another.
            </p>
            <p className="specimen-abc" style={{ fontFamily: data.cssFamily }}>
              Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll Mm<br />
              Nn Oo Pp Qq Rr Ss Tt Uu Vv Ww Xx Yy Zz
            </p>
          </div>

          <p className="font-body-text">{data.bodyText}</p>

          <div className="font-features" aria-label="Key design features">
            {data.features.map(feat => (
              <div className="font-feat" key={feat}>
                <div className="feat-dot" aria-hidden="true" />
                <span>{feat}</span>
              </div>
            ))}
          </div>

          <div className="font-link-row">
            <span className="font-credit">
              Designed by <strong>{data.credit.designer}</strong>
            </span>
            <a
              href={data.credit.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-link"
            >
              {data.credit.urlLabel}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                aria-hidden="true">
                <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </a>
          </div>

        </div>
      )}

    </section>
  )
}
