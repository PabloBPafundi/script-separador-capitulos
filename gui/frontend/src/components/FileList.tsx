import { useEffect, useState } from 'react'
import { api } from '../api'
import { Icon } from './Icon'
import { basename } from '../utils'

interface Props {
  pdfPaths: string[]
  onChange: (paths: string[]) => void
  disabled: boolean
}

export function FileList({ pdfPaths, onChange, disabled }: Props) {
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    window.__onPdfsDropped = (paths) => {
      if (paths.length === 0) return
      onChange(Array.from(new Set([...pdfPaths, ...paths])))
    }
    return () => {
      window.__onPdfsDropped = undefined
    }
  }, [pdfPaths, onChange])

  async function handleAdd() {
    const picked = await api.pickPdfs()
    if (picked.length === 0) return
    onChange(Array.from(new Set([...pdfPaths, ...picked])))
  }

  function handleRemove(path: string) {
    onChange(pdfPaths.filter((p) => p !== path))
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>
          <Icon name="file" className="icon-heading" />
          1. Elegí los PDFs
          {pdfPaths.length > 0 && <span className="count-badge">{pdfPaths.length}</span>}
        </h2>
        <button className="btn" onClick={handleAdd} disabled={disabled}>
          Agregar PDFs…
        </button>
      </div>

      <div
        className={`dropzone ${pdfPaths.length === 0 ? 'dropzone-empty' : ''} ${dragging ? 'dropzone-active' : ''} ${disabled ? 'dropzone-disabled' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
        }}
      >
        <Icon name="upload-cloud" className="dropzone-icon" />
        {pdfPaths.length === 0 ? (
          <p className="hint">
            Arrastrá uno o varios PDFs acá, o usá "Agregar PDFs…" (podés elegir varios a la vez).
          </p>
        ) : (
          <ul className="file-list">
            {pdfPaths.map((path) => (
              <li key={path}>
                <Icon name="file" className="icon-sm file-list-icon" />
                <span className="file-list-name" title={path}>
                  {basename(path)}
                </span>
                <button
                  type="button"
                  className="btn-icon"
                  title="Quitar de la lista"
                  onClick={() => handleRemove(path)}
                  disabled={disabled}
                >
                  <Icon name="x" className="icon-sm" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
