export function basename(path: string): string {
  return path.split(/[\\/]/).pop() ?? path
}

export function stem(path: string): string {
  const name = basename(path)
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(0, dot) : name
}

/** Formatea un rango de páginas en base cero como texto legible en español. */
export function formatPageRange(startPage: number, endPage: number): string {
  const start = startPage + 1
  const end = endPage + 1
  return start === end ? `pág. ${start}` : `págs. ${start}–${end}`
}
