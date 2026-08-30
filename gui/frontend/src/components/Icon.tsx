interface Props {
  name: string
  className?: string
}

export function Icon({ name, className }: Props) {
  return (
    <svg className={`icon ${className ?? ''}`} aria-hidden="true">
      <use href={`./app-icons.svg#icon-${name}`} />
    </svg>
  )
}
