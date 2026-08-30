import { api } from '../api'
import type { FileRunStatus, JobStatus } from '../api'
import { Icon } from './Icon'

interface Props {
  job: JobStatus | null
}

const STATUS_LABEL: Record<string, string> = {
  pending: 'En espera',
  running: 'Procesando…',
  done: 'Listo',
  error: 'Error',
}

const STATUS_ICON: Record<FileRunStatus, string> = {
  pending: 'loader',
  running: 'loader',
  done: 'check-circle',
  error: 'alert-circle',
}

export function ResultsPanel({ job }: Props) {
  if (job === null) return null

  const total = job.files.length
  const finished = job.files.filter((f) => f.status === 'done' || f.status === 'error').length
  const progressPercent = total > 0 ? Math.round((finished / total) * 100) : 0

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>
          <Icon name="check-circle" className="icon-heading" />
          6. Resultado
        </h2>
      </div>

      {job.status === 'running' && (
        <div className="progress-summary">
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }} />
          </div>
          <span className="hint">
            Procesando {finished} de {total} PDF{total === 1 ? '' : 's'}…
          </span>
        </div>
      )}

      <ul className="result-list">
        {job.files.map((file) => (
          <li key={file.path} className={`result-item result-${file.status}`}>
            <div className="result-main">
              <span className="result-name">
                <Icon
                  name={STATUS_ICON[file.status]}
                  className={`icon-sm result-icon ${file.status === 'running' ? 'icon-spin' : ''}`}
                />
                {file.name}
              </span>
              <span className="result-status">{STATUS_LABEL[file.status] ?? file.status}</span>
            </div>
            {file.status === 'done' && (
              <div className="result-detail">
                <span>{file.chapters} capítulos generados</span>
                <button className="btn-link" onClick={() => api.openPath(file.output_dir)}>
                  <Icon name="external-link" className="icon-sm" />
                  Abrir carpeta
                </button>
              </div>
            )}
            {file.status === 'error' && <div className="result-detail result-error-text">{file.error}</div>}
          </li>
        ))}
      </ul>
    </section>
  )
}
