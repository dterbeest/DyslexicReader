import { useState } from 'react'

export default function OpenDyslexicInfo() {
  const [open, setOpen] = useState(false)

  return (
    <section className="font-info anim-3" aria-label="About OpenDyslexic">

      <button
        className="font-info-toggle"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <div className="font-info-mark" aria-hidden="true">Aa</div>
        <div className="font-info-toggle-label">
          <div className="font-info-toggle-title">About OpenDyslexic</div>
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
              <h2 className="font-info-title">OpenDyslexic</h2>
              <p className="font-info-sub">Designed to reduce common reading difficulties</p>
            </div>
          </div>

          <div className="font-specimen">
            <div className="specimen-label">Font specimen</div>
            <p className="specimen-text">
              Reading should feel easy. Every letter has a unique shape
              so your eye never confuses one for another.
            </p>
            <p className="specimen-abc">
              Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll Mm<br />
              Nn Oo Pp Qq Rr Ss Tt Uu Vv Ww Xx Yy Zz
            </p>
          </div>

          <p className="font-body-text">
            OpenDyslexic is a free, open-source typeface created by <strong>Abbie Gonzalez</strong>,
            designed to reduce some of the common reading difficulties associated with dyslexia.
            Each character has a unique shape and a heavy weighted bottom that anchors
            letters to the baseline — preventing them from visually rotating or flipping.
          </p>

          <div className="font-features" aria-label="Key design features">
            <div className="font-feat">
              <div className="feat-dot" aria-hidden="true" />
              <span>Heavy bottoms anchor letters to the baseline</span>
            </div>
            <div className="font-feat">
              <div className="feat-dot" aria-hidden="true" />
              <span>Unique shapes reduce b/d and p/q confusion</span>
            </div>
            <div className="font-feat">
              <div className="feat-dot" aria-hidden="true" />
              <span>Wider spacing aids word recognition</span>
            </div>
            <div className="font-feat">
              <div className="feat-dot" aria-hidden="true" />
              <span>Free and open source — SIL Open Font License</span>
            </div>
          </div>

          <div className="font-link-row">
            <span className="font-credit">
              Designed by <strong>Abbie Gonzalez</strong>
            </span>
            <a
              href="https://opendyslexic.org"
              target="_blank"
              rel="noopener noreferrer"
              className="font-link"
            >
              opendyslexic.org
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
