interface SwipeOptions {
  onSwipeRight?: () => void
  onSwipeLeft?: () => void
  edgeOnly?: boolean
  edgeWidth?: number
  threshold?: number
}

export function useSwipeGesture(options: SwipeOptions) {
  const { onSwipeRight, onSwipeLeft, edgeOnly = false, edgeWidth = 30, threshold = 60 } = options

  let startX = 0
  let startY = 0
  let isEdgeSwipe = false

  function handleTouchStart(e: TouchEvent) {
    const touch = e.touches[0]
    startX = touch.clientX
    startY = touch.clientY
    isEdgeSwipe = !edgeOnly || startX < edgeWidth
  }

  function handleTouchEnd(e: TouchEvent) {
    if (!isEdgeSwipe) return

    const touch = e.changedTouches[0]
    const dx = touch.clientX - startX
    const dy = Math.abs(touch.clientY - startY)

    // Ignore if vertical movement is greater than horizontal
    if (dy > Math.abs(dx)) return

    if (dx > threshold && onSwipeRight) {
      onSwipeRight()
    } else if (dx < -threshold && onSwipeLeft) {
      onSwipeLeft()
    }
  }

  document.addEventListener('touchstart', handleTouchStart, { passive: true })
  document.addEventListener('touchend', handleTouchEnd, { passive: true })

  function cleanup() {
    document.removeEventListener('touchstart', handleTouchStart)
    document.removeEventListener('touchend', handleTouchEnd)
  }

  return { cleanup }
}
