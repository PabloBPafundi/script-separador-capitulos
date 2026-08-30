import { useState } from 'react'
import type { PipelineSettings } from '../api'
import { Icon } from './Icon'
import { Tooltip } from './Tooltip'

interface Props {
  settings: PipelineSettings
  onChange: (settings: PipelineSettings) => void
  disabled: boolean
  defaultRegexPatterns: string[] | null
}

export function SettingsPanel({ settings, onChange, disabled, defaultRegexPatterns }: Props) {
  const [expanded, setExpanded] = useState(false)

  function set<K extends keyof PipelineSettings>(key: K, value: PipelineSettings[K]) {
    onChange({ ...settings, [key]: value })
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>
          <Icon name="sliders" className="icon-heading" />
          3. Ajustes de detección (opcional)
        </h2>
        <button
          type="button"
          className="btn-link"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          {expanded ? 'Ocultar' : 'Mostrar'}
          <Icon name="chevron-down" className={`icon-sm chevron ${expanded ? 'chevron-open' : ''}`} />
        </button>
      </div>

      {expanded && (
        <div className="settings-grid">
          <label className="option-toggle">
            <input
              type="checkbox"
              checked={settings.use_toc_first}
              disabled={disabled}
              onChange={(e) => set('use_toc_first', e.target.checked)}
            />
            <span>
              Usar el índice/bookmarks del PDF si existe
              <Tooltip text="Si el PDF trae un índice (tabla de contenidos) embebido, se usa para ubicar el inicio de cada capítulo. Es el método más confiable cuando está disponible." />
            </span>
          </label>

          <label className="option-toggle">
            <input
              type="checkbox"
              checked={settings.use_typographic_chapter_detection}
              disabled={disabled}
              onChange={(e) => set('use_typographic_chapter_detection', e.target.checked)}
            />
            <span>
              Detectar encabezados tipo "CHAPTER I" (OCR)
              <Tooltip text="Busca líneas en mayúsculas con un marcador de capítulo (por ejemplo CHAPTER I) y las combina con el título que sigue. Útil para libros escaneados sin índice." />
            </span>
          </label>

          <label className="option-toggle">
            <input
              type="checkbox"
              checked={settings.include_title_in_filename}
              disabled={disabled}
              onChange={(e) => set('include_title_in_filename', e.target.checked)}
            />
            <span>
              Incluir el título del capítulo en el nombre de archivo
              <Tooltip text="Si está desactivado, los archivos se numeran usando el prefijo de abajo (por ejemplo Capitulo_001.pdf) en vez del título detectado." />
            </span>
          </label>

          <label className="option-toggle">
            <input
              type="checkbox"
              checked={settings.overwrite_existing_files}
              disabled={disabled}
              onChange={(e) => set('overwrite_existing_files', e.target.checked)}
            />
            <span>
              Sobrescribir archivos existentes
              <Tooltip text="Si ya existe un archivo con ese nombre en la carpeta de salida, se reemplaza. Si lo desactivás, la corrida se detiene con un error ante un archivo repetido." />
            </span>
          </label>

          <label className="field">
            <span className="field-label">
              Prefijo de archivo (si no se incluye el título)
              <Tooltip text="Nombre base para los PDF generados cuando 'Incluir el título del capítulo en el nombre de archivo' está desactivado. Por ejemplo, con el prefijo Capitulo se generan Capitulo_001.pdf, Capitulo_002.pdf, etc." />
            </span>
            <input
              type="text"
              value={settings.file_prefix}
              disabled={disabled}
              onChange={(e) => set('file_prefix', e.target.value)}
            />
          </label>

          <label className="field">
            <span className="field-label">
              Dígitos de numeración
              <Tooltip text="Cantidad de dígitos con los que se numeran los archivos generados. Con 3 dígitos, por ejemplo, el primer capítulo queda como 001." />
            </span>
            <input
              type="number"
              min={1}
              max={6}
              value={settings.chapter_number_padding}
              disabled={disabled}
              onChange={(e) => set('chapter_number_padding', Number(e.target.value))}
            />
          </label>

          <label className="field">
            <span className="field-label">
              Tamaño mínimo de fuente del título (detección OCR)
              <Tooltip text="Al detectar encabezados tipo 'CHAPTER I', solo se consideran parte del título las líneas en mayúscula con una tipografía de al menos este tamaño. Subilo si agarra texto de más; bajalo si le falta parte del título." />
            </span>
            <input
              type="number"
              min={1}
              step={0.5}
              value={settings.chapter_title_min_font_size}
              disabled={disabled}
              onChange={(e) => set('chapter_title_min_font_size', Number(e.target.value))}
            />
          </label>

          <label className="field">
            <span className="field-label">
              Expresiones regulares de respaldo (una por línea)
              <Tooltip text="Se usan solo si no hay índice ni encabezados detectables. Cada línea es una expresión regular que busca el inicio de un capítulo en el texto de cada página. Si las borrás sin querer, podés recuperar las originales con 'Restaurar'." />
              {defaultRegexPatterns && (
                <button
                  type="button"
                  className="btn-link field-reset"
                  disabled={disabled}
                  onClick={() => set('chapter_regex_patterns', defaultRegexPatterns)}
                >
                  Restaurar
                </button>
              )}
            </span>
            <textarea
              rows={4}
              value={settings.chapter_regex_patterns.join('\n')}
              disabled={disabled}
              onChange={(e) => set('chapter_regex_patterns', e.target.value.split('\n'))}
            />
          </label>
        </div>
      )}
    </section>
  )
}
