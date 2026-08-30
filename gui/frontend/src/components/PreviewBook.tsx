import type { PreviewFile } from '../api'
import { Icon } from './Icon'
import { formatPageRange } from '../utils'

interface Props {
  file: PreviewFile
  expanded: boolean
  onToggleExpanded: () => void
  onToggleChapter: (chapterIndex: number) => void
  onRenameChapter: (chapterIndex: number, title: string) => void
  onToggleAll: (included: boolean) => void
  disabled: boolean
}

const STATUS_ICON: Record<string, string> = {
  pending: 'loader',
  running: 'loader',
  done: 'check-circle',
  error: 'alert-circle',
}

export function PreviewBook({
  file,
  expanded,
  onToggleExpanded,
  onToggleChapter,
  onRenameChapter,
  onToggleAll,
  disabled,
}: Props) {
  const isBusy = file.status === 'pending' || file.status === 'running'
  const includedCount = file.chapters.filter((c) => c.included).length
  const nothingSelected = file.status === 'done' && file.chapters.length > 0 && includedCount === 0

  return (
    <div className={`preview-book preview-book-${file.status}`}>
      <button
        type="button"
        className="preview-book-header"
        onClick={onToggleExpanded}
        disabled={isBusy || file.status === 'error'}
      >
        <Icon name={STATUS_ICON[file.status]} className={`icon-sm preview-book-icon ${isBusy ? 'icon-spin' : ''}`} />
        <span className="preview-book-name">{file.name}</span>
        {file.status === 'done' && (
          <span className={`count-badge ${nothingSelected ? 'count-badge-danger' : ''}`}>
            {includedCount}/{file.chapters.length}
          </span>
        )}
        {isBusy && <span className="hint">Detectando…</span>}
        {file.status === 'done' && (
          <Icon name="chevron-down" className={`icon-sm chevron ${expanded ? 'chevron-open' : ''}`} />
        )}
      </button>

      {file.status === 'error' && (
        <p className="hint preview-book-error">
          <Icon name="alert-circle" className="icon-sm" />
          {file.error}
        </p>
      )}

      {nothingSelected && (
        <p className="hint preview-book-error">
          <Icon name="alert-circle" className="icon-sm" />
          Deseleccionaste todos los capítulos: este PDF no se va a exportar.
        </p>
      )}

      {file.status === 'done' && expanded && (
        <div className="preview-book-body">
          <div className="preview-book-toolbar">
            <button type="button" className="btn-link" disabled={disabled} onClick={() => onToggleAll(true)}>
              Seleccionar todos
            </button>
            <button type="button" className="btn-link" disabled={disabled} onClick={() => onToggleAll(false)}>
              Ninguno
            </button>
          </div>
          <ul className="preview-chapter-list">
            {file.chapters.map((chapter, index) => (
              <li key={index} className={`preview-chapter-row ${chapter.included ? '' : 'preview-chapter-excluded'}`}>
                <input
                  type="checkbox"
                  checked={chapter.included}
                  disabled={disabled}
                  onChange={() => onToggleChapter(index)}
                  aria-label={`Incluir "${chapter.title}"`}
                />
                <span className="preview-chapter-pages">
                  {formatPageRange(chapter.start_page, chapter.end_page)}
                </span>
                <input
                  type="text"
                  className="preview-chapter-title"
                  value={chapter.title}
                  disabled={disabled || !chapter.included}
                  onChange={(e) => onRenameChapter(index, e.target.value)}
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
