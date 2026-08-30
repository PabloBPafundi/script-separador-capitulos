interface Props {
  onDone: () => void
}

export function Splash({ onDone }: Props) {
  return (
    <div
      className="splash"
      onAnimationEnd={(e) => {
        if (e.animationName === 'splash-out') onDone()
      }}
    >
      <img src="./favicon.svg" alt="" className="splash-logo" />
      <h1 className="splash-title">PDF Chapter Splitter</h1>
    </div>
  )
}
