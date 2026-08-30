import { useId } from 'react'
import { Icon } from './Icon'

interface Props {
  text: string
}

export function Tooltip({ text }: Props) {
  const id = useId()

  return (
    <span className="tooltip">
      <button type="button" className="tooltip-trigger" aria-describedby={id}>
        <Icon name="info" className="icon-sm" />
      </button>
      <span role="tooltip" id={id} className="tooltip-bubble">
        {text}
      </span>
    </span>
  )
}
