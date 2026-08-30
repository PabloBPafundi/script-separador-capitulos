import { useEffect, useRef, useState } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import { api } from '../api'
import type { PipelineSettings, PreviewFile } from '../api'
import { Icon } from './Icon'
import { Tooltip } from './Tooltip'
import { PreviewBook } from './PreviewBook'
import { basename } from '../utils'

interface Props {
  pdfPaths: string[]
  settings: PipelineSettings
  preview: PreviewFile[] | null
  onPreviewChange: Dispatch<SetStateAction<PreviewFile[] | null>>
  disabled: boolean
}

const POLL_INTERVAL_MS = 400

export function PreviewPanel({ pdfPaths, settings, preview, onPreviewChange, disabled }: Props) {
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set())
  const detectGeneration = useRef(0)

  // Si algo invalidó la vista previa desde afuera (cambiaron los PDFs o los
  // ajustes de detección), cualquier detección en curso deja de aplicar sus
  // resultados: evita "resucitar" una vista previa que ya no corresponde.
  useEffect(() => {
    if (preview === null) detectGeneration.current += 1
  }, [preview])

  const isDetecting = preview !== null && preview.some((f) => f.status === 'pending' || f.status === 'running')

  async function handleDetect() {
    const generation = ++detectGeneration.current
    setCollapsed(new Set())
    onPreviewChange(
      pdfPaths.map((path) => ({ path, name: basename(path), status: 'pending', error: null, chapters: [] })),
    )
    const jobId = await api.startPreview(pdfPaths, settings)
    poll(jobId, generation)
  }

  function poll(jobId: string, generation: number) {
    api.getPreviewStatus(jobId).then((status) => {
      if (detectGeneration.current !== generation) return
      onPreviewChange((current) =>
        pdfPaths.map((path, i) => {
          const previous = current?.[i]
          // Un libro ya detectado puede estar siendo renombrado o filtrado por
          // el usuario mientras los demás siguen procesándose: sus resultados
          // ya no cambian, así que conservamos sus ediciones tal cual.
          if (previous?.status === 'done') return previous
          const f = status.files[i]
          if (f === undefined) {
            return previous ?? { path, name: basename(path), status: 'pending', error: null, chapters: [] }
          }
          return {
            path,
            name: f.name,
            status: f.status,
            error: f.error,
            chapters: f.chapters.map((c) => ({ ...c, included: true })),
          }
        }),
      )
      if (status.status === 'running') {
        window.setTimeout(() => poll(jobId, generation), POLL_INTERVAL_MS)
      }
    })
  }

  function updateFile(index: number, updater: (file: PreviewFile) => PreviewFile) {
    if (!preview) return
    onPreviewChange(preview.map((f, i) => (i === index ? updater(f) : f)))
  }

  const totals = preview?.reduce(
    (acc, f) => {
      acc.total += f.chapters.length
      acc.included += f.chapters.filter((c) => c.included).length
      return acc
    },
    { total: 0, included: 0 },
  )

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>
          <Icon name="eye" className="icon-heading" />
          4. Vista previa de capítulos (opcional)
          <Tooltip text="Detecta los capítulos sin exportar todavía. Podés renombrarlos o excluir alguno antes de dividir el PDF de verdad." />
        </h2>
        {preview !== null && !isDetecting && (
          <button
            type="button"
            className="btn-link"
            onClick={handleDetect}
            disabled={disabled || pdfPaths.length === 0}
          >
            <Icon name="refresh" className="icon-sm" />
            Detectar de nuevo
          </button>
        )}
      </div>

      {preview === null && (
        <div className="preview-empty">
          <p className="hint">
            Mirá qué capítulos va a generar cada PDF antes de exportar: podés renombrarlos o excluir alguno.
          </p>
          <button
            type="button"
            className="btn"
            onClick={handleDetect}
            disabled={disabled || pdfPaths.length === 0}
          >
            <Icon name="eye" className="icon-sm" />
            Detectar capítulos
          </button>
        </div>
      )}

      {preview !== null && (
        <>
          <div className="preview-books">
            {preview.map((file, index) => (
              <PreviewBook
                key={file.path}
                file={file}
                expanded={!collapsed.has(index)}
                onToggleExpanded={() =>
                  setCollapsed((prev) => {
                    const next = new Set(prev)
                    if (next.has(index)) next.delete(index)
                    else next.add(index)
                    return next
                  })
                }
                onToggleChapter={(chapterIndex) =>
                  updateFile(index, (f) => ({
                    ...f,
                    chapters: f.chapters.map((c, i) =>
                      i === chapterIndex ? { ...c, included: !c.included } : c,
                    ),
                  }))
                }
                onRenameChapter={(chapterIndex, title) =>
                  updateFile(index, (f) => ({
                    ...f,
                    chapters: f.chapters.map((c, i) => (i === chapterIndex ? { ...c, title } : c)),
                  }))
                }
                onToggleAll={(included) =>
                  updateFile(index, (f) => ({
                    ...f,
                    chapters: f.chapters.map((c) => ({ ...c, included })),
                  }))
                }
                disabled={disabled}
              />
            ))}
          </div>

          {totals !== undefined && totals.total > 0 && (
            <p className="hint preview-summary">
              {totals.included} de {totals.total} capítulos seleccionados para exportar.
            </p>
          )}
        </>
      )}
    </section>
  )
}
