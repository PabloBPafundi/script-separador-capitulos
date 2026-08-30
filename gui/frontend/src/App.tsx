import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { ChapterRange, JobStatus, OutputOrganization, PipelineSettings, PreviewFile, UpdateCheck } from './api'
import { FileList } from './components/FileList'
import { basename } from './utils'
import { OutputOrganizationPanel } from './components/OutputOrganizationPanel'
import { SettingsPanel } from './components/SettingsPanel'
import { PreviewPanel } from './components/PreviewPanel'
import { RunPanel } from './components/RunPanel'
import { ResultsPanel } from './components/ResultsPanel'
import { UpdateBanner } from './components/UpdateBanner'
import { Splash } from './components/Splash'
import { Icon } from './components/Icon'

function buildChaptersByFile(preview: PreviewFile[] | null): Record<string, ChapterRange[]> | undefined {
  if (preview === null) return undefined
  const map: Record<string, ChapterRange[]> = {}
  for (const file of preview) {
    if (file.status !== 'done') continue
    map[file.path] = file.chapters
      .filter((c) => c.included)
      .map(({ title, start_page, end_page }) => ({ title, start_page, end_page }))
  }
  return map
}

const POLL_INTERVAL_MS = 500

function App() {
  const [showSplash, setShowSplash] = useState(true)
  const [pdfPaths, setPdfPaths] = useState<string[]>([])
  const [outputDir, setOutputDir] = useState<string | null>(null)
  const [settings, setSettings] = useState<PipelineSettings | null>(null)
  const [defaultRegexPatterns, setDefaultRegexPatterns] = useState<string[] | null>(null)
  const [output, setOutput] = useState<OutputOrganization>({ createBookFolder: true, bookFolderName: '' })
  const [preview, setPreview] = useState<PreviewFile[] | null>(null)
  // Rastrea con qué PDFs/ajustes se generó la vista previa actual, ajustado
  // durante el render (no en un efecto) siguiendo el patrón de React para
  // "resetear estado cuando cambia una prop": evita un ciclo extra de commit.
  const [previewInputs, setPreviewInputs] = useState({ pdfPaths, settings })
  if (previewInputs.pdfPaths !== pdfPaths || previewInputs.settings !== settings) {
    setPreviewInputs({ pdfPaths, settings })
    setPreview(null)
  }
  const [jobId, setJobId] = useState<string | null>(null)
  const [job, setJob] = useState<JobStatus | null>(null)
  const [version, setVersion] = useState('')
  const [update, setUpdate] = useState<UpdateCheck>({ available: false })
  const [showSaved, setShowSaved] = useState(false)
  const pollRef = useRef<number | null>(null)
  const isFirstSettingsSave = useRef(true)
  const savedPulseTimeout = useRef<number | null>(null)

  useEffect(() => {
    // Ajustes guardados de una corrida anterior (o los de fábrica si es la
    // primera vez). Los de fábrica se piden aparte, sin la personalización
    // del usuario, para poder ofrecer un botón de "Restaurar".
    api.getDefaultSettings().then(setSettings)
    api.getFactoryDefaults().then((factory) => setDefaultRegexPatterns(factory.chapter_regex_patterns))
    api.getAppVersion().then(setVersion)
    api.checkForUpdates().then(setUpdate).catch(() => undefined)
  }, [])

  useEffect(() => {
    if (settings === null) return
    // Guarda en disco los ajustes tras una breve pausa de inactividad, para
    // que la próxima vez que se abra la app arranque donde quedó el usuario.
    // No hay botón de guardar: el aviso "Guardado" es la única confirmación.
    const skipPulse = isFirstSettingsSave.current
    isFirstSettingsSave.current = false
    const timeout = window.setTimeout(() => {
      api.saveSettings(settings).then(() => {
        if (skipPulse) return
        setShowSaved(true)
        if (savedPulseTimeout.current !== null) window.clearTimeout(savedPulseTimeout.current)
        savedPulseTimeout.current = window.setTimeout(() => setShowSaved(false), 1800)
      })
    }, 600)
    return () => window.clearTimeout(timeout)
  }, [settings])

  useEffect(() => {
    if (jobId === null) return

    function poll() {
      api.getJobStatus(jobId!).then((status) => {
        setJob(status)
        if (status.status === 'running') {
          pollRef.current = window.setTimeout(poll, POLL_INTERVAL_MS)
        }
      })
    }
    poll()

    return () => {
      if (pollRef.current !== null) window.clearTimeout(pollRef.current)
    }
  }, [jobId])

  const running = job?.status === 'running'

  const previewHasEmptySelection =
    preview?.some((f) => f.status === 'done' && f.chapters.length > 0 && f.chapters.every((c) => !c.included)) ??
    false

  async function handleRun() {
    if (settings === null || outputDir === null || pdfPaths.length === 0 || previewHasEmptySelection) return
    // Feedback inmediato: no esperamos al primer poll para mostrar que ya está
    // procesando, útil con PCs lentas o muchos PDFs en la cola.
    setJob({
      status: 'running',
      files: pdfPaths.map((path) => ({
        path,
        name: basename(path),
        status: 'pending',
        chapters: 0,
        output_dir: '',
        error: null,
      })),
      logs: [],
    })
    const chaptersByFile = buildChaptersByFile(preview)
    const id = await api.startJob(pdfPaths, outputDir, settings, output, chaptersByFile)
    setJobId(id)
  }

  return (
    <>
      {showSplash && <Splash onDone={() => setShowSplash(false)} />}
      <div className="app">
        <header className="app-header">
          <div className="app-brand">
            <img src="./favicon.svg" alt="" className="app-logo" />
            <h1>PDF Chapter Splitter</h1>
          </div>
          <div className="app-header-right">
            <span className={`save-indicator ${showSaved ? 'save-indicator-visible' : ''}`} aria-live="polite">
              <Icon name="check-circle" className="icon-sm" />
              Guardado
            </span>
            <span className="version">v{version}</span>
          </div>
        </header>

        <UpdateBanner update={update} />

        <FileList pdfPaths={pdfPaths} onChange={setPdfPaths} disabled={running} />

        {settings && (
          <OutputOrganizationPanel
            settings={settings}
            onSettingsChange={setSettings}
            output={output}
            onOutputChange={setOutput}
            pdfPaths={pdfPaths}
            disabled={running}
          />
        )}

        {settings && (
          <SettingsPanel
            settings={settings}
            onChange={setSettings}
            disabled={running}
            defaultRegexPatterns={defaultRegexPatterns}
          />
        )}

        {settings && (
          <PreviewPanel
            pdfPaths={pdfPaths}
            settings={settings}
            preview={preview}
            onPreviewChange={setPreview}
            disabled={running}
          />
        )}

        <RunPanel
          outputDir={outputDir}
          onPickOutputDir={setOutputDir}
          canRun={pdfPaths.length > 0 && outputDir !== null && !previewHasEmptySelection}
          running={running}
          onRun={handleRun}
          warning={
            previewHasEmptySelection
              ? 'Hay un PDF sin capítulos seleccionados en la vista previa: incluí al menos uno o volvé a detectar.'
              : undefined
          }
        />

        <ResultsPanel job={job} />
      </div>
    </>
  )
}

export default App
