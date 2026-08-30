import { api } from '../api'
import { Icon } from './Icon'

interface Props {
  outputDir: string | null
  onPickOutputDir: (dir: string) => void
  canRun: boolean
  running: boolean
  onRun: () => void
  warning?: string
}

export function RunPanel({ outputDir, onPickOutputDir, canRun, running, onRun, warning }: Props) {
  async function handlePick() {
    const dir = await api.pickOutputDir()
    if (dir) onPickOutputDir(dir)
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>
          <Icon name="folder" className="icon-heading" />
          5. Carpeta de salida y ejecución
        </h2>
      </div>
      <div className="run-row">
        <button className="btn" onClick={handlePick} disabled={running}>
          <Icon name="folder" className="icon-sm" />
          {outputDir ? 'Cambiar carpeta…' : 'Elegir carpeta de salida…'}
        </button>
        <span className="hint output-dir-hint" title={outputDir ?? undefined}>
          {outputDir ?? 'No se eligió ninguna carpeta.'}
        </span>
      </div>
      <button className="btn btn-primary btn-run" onClick={onRun} disabled={!canRun || running}>
        <Icon name={running ? 'loader' : 'play'} className={`icon-sm ${running ? 'icon-spin' : ''}`} />
        {running ? 'Procesando…' : 'Dividir capítulos'}
      </button>
      {warning && !running && (
        <p className="hint run-warning">
          <Icon name="alert-circle" className="icon-sm" />
          {warning}
        </p>
      )}
    </section>
  )
}
