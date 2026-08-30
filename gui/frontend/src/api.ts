export interface PipelineSettings {
  file_prefix: string
  include_title_in_filename: boolean
  chapter_number_padding: number
  use_toc_first: boolean
  toc_chapter_level: number
  use_typographic_chapter_detection: boolean
  chapter_title_min_font_size: number
  chapter_title_max_lines: number
  chapter_regex_patterns: string[]
  regex_scan_characters: number | null
  overwrite_existing_files: boolean
  separate_folder_per_chapter: boolean
}

export interface OutputOrganization {
  createBookFolder: boolean
  bookFolderName: string
}

export type FileRunStatus = 'pending' | 'running' | 'done' | 'error'

export interface FileStatus {
  path: string
  name: string
  status: FileRunStatus
  chapters: number
  output_dir: string
  error: string | null
}

export interface JobStatus {
  status: 'running' | 'done' | 'error' | 'unknown'
  files: FileStatus[]
  logs: string[]
}

export interface UpdateCheck {
  available: boolean
  version?: string
  url?: string
}

export interface ChapterRange {
  title: string
  start_page: number
  end_page: number
}

export type PreviewRunStatus = 'pending' | 'running' | 'done' | 'error'

export interface PreviewFileResult {
  name: string
  status: PreviewRunStatus
  chapters: ChapterRange[]
  error: string | null
}

export interface PreviewJobStatus {
  status: 'running' | 'done' | 'error' | 'unknown'
  files: PreviewFileResult[]
}

/** Capítulo tal como lo edita el usuario en la vista previa (con inclusión). */
export interface PreviewChapter extends ChapterRange {
  included: boolean
}

/** Estado por libro de la vista previa, mantenido en el frontend. */
export interface PreviewFile {
  path: string
  name: string
  status: PreviewRunStatus
  error: string | null
  chapters: PreviewChapter[]
}

interface PywebviewApi {
  pick_pdfs(): Promise<string[]>
  pick_output_dir(): Promise<string | null>
  get_default_settings(): Promise<PipelineSettings>
  get_factory_defaults(): Promise<PipelineSettings>
  save_settings(settings: PipelineSettings): Promise<void>
  get_app_version(): Promise<string>
  start_preview(pdfPaths: string[], settings: PipelineSettings): Promise<string>
  get_preview_status(jobId: string): Promise<PreviewJobStatus>
  start_job(
    pdfPaths: string[],
    outputDir: string,
    settings: PipelineSettings,
    createBookFolder: boolean,
    bookFolderName: string,
    chaptersByFile?: Record<string, ChapterRange[]>,
  ): Promise<string>
  get_job_status(jobId: string): Promise<JobStatus>
  open_path(path: string): Promise<void>
  check_for_updates(): Promise<UpdateCheck>
  apply_update(): Promise<{ ok: boolean; error?: string }>
}

declare global {
  interface Window {
    pywebview?: { api: PywebviewApi }
    __onPdfsDropped?: (paths: string[]) => void
  }
}

function waitForPywebview(): Promise<PywebviewApi> {
  if (window.pywebview?.api) {
    return Promise.resolve(window.pywebview.api)
  }
  return new Promise((resolve) => {
    window.addEventListener('pywebviewready', () => resolve(window.pywebview!.api), { once: true })
  })
}

async function callApi<T extends keyof PywebviewApi>(
  method: T,
  ...args: Parameters<PywebviewApi[T]>
): Promise<Awaited<ReturnType<PywebviewApi[T]>>> {
  const api = await waitForPywebview()
  // @ts-expect-error -- el spread de args coincide con la firma de cada método.
  return api[method](...args)
}

export const api = {
  pickPdfs: () => callApi('pick_pdfs'),
  pickOutputDir: () => callApi('pick_output_dir'),
  getDefaultSettings: () => callApi('get_default_settings'),
  getFactoryDefaults: () => callApi('get_factory_defaults'),
  saveSettings: (settings: PipelineSettings) => callApi('save_settings', settings),
  getAppVersion: () => callApi('get_app_version'),
  startPreview: (pdfPaths: string[], settings: PipelineSettings) =>
    callApi('start_preview', pdfPaths, settings),
  getPreviewStatus: (jobId: string) => callApi('get_preview_status', jobId),
  startJob: (
    pdfPaths: string[],
    outputDir: string,
    settings: PipelineSettings,
    output: OutputOrganization,
    chaptersByFile?: Record<string, ChapterRange[]>,
  ) =>
    callApi(
      'start_job',
      pdfPaths,
      outputDir,
      settings,
      output.createBookFolder,
      output.bookFolderName,
      chaptersByFile,
    ),
  getJobStatus: (jobId: string) => callApi('get_job_status', jobId),
  openPath: (path: string) => callApi('open_path', path),
  checkForUpdates: () => callApi('check_for_updates'),
  applyUpdate: () => callApi('apply_update'),
}
