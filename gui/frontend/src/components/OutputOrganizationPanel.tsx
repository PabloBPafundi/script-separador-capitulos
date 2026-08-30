import type { OutputOrganization, PipelineSettings } from '../api'
import { Icon } from './Icon'
import { Tooltip } from './Tooltip'
import { stem } from '../utils'

interface Props {
  settings: PipelineSettings
  onSettingsChange: (settings: PipelineSettings) => void
  output: OutputOrganization
  onOutputChange: (output: OutputOrganization) => void
  pdfPaths: string[]
  disabled: boolean
}

export function OutputOrganizationPanel({
  settings,
  onSettingsChange,
  output,
  onOutputChange,
  pdfPaths,
  disabled,
}: Props) {
  const singleFile = pdfPaths.length === 1

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>
          <Icon name="layers" className="icon-heading" />
          2. Organización de la salida
        </h2>
      </div>

      <div className="option-group">
        <span className="option-group-label">
          ¿Dónde van los capítulos de cada libro?
          <Tooltip text="Elegí si todos los PDF de capítulos quedan sueltos en la misma carpeta, o si cada capítulo recibe su propia carpeta (útil si además guardás imágenes u otros archivos junto a cada capítulo)." />
        </span>
        <div className="segmented">
          <button
            type="button"
            className={`segmented-option ${!settings.separate_folder_per_chapter ? 'active' : ''}`}
            disabled={disabled}
            onClick={() => onSettingsChange({ ...settings, separate_folder_per_chapter: false })}
          >
            <Icon name="folder" />
            Misma carpeta
          </button>
          <button
            type="button"
            className={`segmented-option ${settings.separate_folder_per_chapter ? 'active' : ''}`}
            disabled={disabled}
            onClick={() => onSettingsChange({ ...settings, separate_folder_per_chapter: true })}
          >
            <Icon name="folders" />
            Una carpeta por capítulo
          </button>
        </div>
      </div>

      <label className="option-toggle">
        <input
          type="checkbox"
          checked={output.createBookFolder}
          disabled={disabled}
          onChange={(e) => onOutputChange({ ...output, createBookFolder: e.target.checked })}
        />
        <span>
          Crear una carpeta con el nombre del libro
          <Tooltip text="Si lo desactivás, los capítulos se guardan directo en la carpeta de salida elegida, sin agrupar por libro." />
        </span>
      </label>

      <div className={`option-detail-collapse ${output.createBookFolder ? '' : 'option-detail-collapsed'}`}>
        <div className="option-detail">
          {singleFile ? (
            <label className="field">
              Nombre de la carpeta (opcional)
              <input
                type="text"
                placeholder={pdfPaths[0] ? stem(pdfPaths[0]) : 'Nombre del libro'}
                value={output.bookFolderName}
                disabled={disabled}
                onChange={(e) => onOutputChange({ ...output, bookFolderName: e.target.value })}
              />
            </label>
          ) : (
            <p className="hint">Con varios PDF, cada libro usa el nombre de su propio archivo.</p>
          )}
        </div>
      </div>
    </section>
  )
}
