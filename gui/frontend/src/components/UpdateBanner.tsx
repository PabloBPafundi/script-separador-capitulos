import { useState } from 'react'
import { api } from '../api'
import type { UpdateCheck } from '../api'
import { Icon } from './Icon'

interface Props {
  update: UpdateCheck
}

export function UpdateBanner({ update }: Props) {
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!update.available) return null

  async function handleUpdate() {
    setApplying(true)
    setError(null)
    const result = await api.applyUpdate()
    // Si `apply_update` tiene éxito, la app se cierra y relanza sola: este
    // código solo se ejecuta si falló antes de llegar a ese punto.
    if (!result.ok) {
      setError(result.error ?? 'No se pudo aplicar la actualización.')
      setApplying(false)
    }
  }

  return (
    <div className="update-banner">
      <Icon name="refresh" className={`icon-sm ${applying ? 'icon-spin' : ''}`} />
      <span>Hay una nueva versión disponible: {update.version}.</span>
      <button className="btn" onClick={handleUpdate} disabled={applying}>
        {applying ? 'Actualizando…' : 'Actualizar ahora'}
      </button>
      {error && <span className="result-error-text">{error}</span>}
    </div>
  )
}
