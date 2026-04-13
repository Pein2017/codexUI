import { onMounted, onUnmounted, ref } from 'vue'

const NARROW_LAYOUT_BREAKPOINT = 640
const MOBILE_BREAKPOINT = 768

function detectMobileLayout(): boolean {
  if (typeof window === 'undefined') return false

  const width = window.innerWidth
  const coarsePointer = window.matchMedia('(pointer: coarse)').matches
    || window.matchMedia('(any-pointer: coarse)').matches

  return width < NARROW_LAYOUT_BREAKPOINT || (coarsePointer && width < MOBILE_BREAKPOINT)
}

export function useMobile() {
  const isMobile = ref(detectMobileLayout())

  let widthMql: MediaQueryList | null = null
  let coarsePointerMql: MediaQueryList | null = null
  let anyCoarsePointerMql: MediaQueryList | null = null

  function syncIsMobile(): void {
    isMobile.value = detectMobileLayout()
  }

  onMounted(() => {
    widthMql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    coarsePointerMql = window.matchMedia('(pointer: coarse)')
    anyCoarsePointerMql = window.matchMedia('(any-pointer: coarse)')

    syncIsMobile()

    widthMql.addEventListener('change', syncIsMobile)
    coarsePointerMql.addEventListener('change', syncIsMobile)
    anyCoarsePointerMql.addEventListener('change', syncIsMobile)
    window.addEventListener('resize', syncIsMobile)
    window.visualViewport?.addEventListener('resize', syncIsMobile)
  })

  onUnmounted(() => {
    widthMql?.removeEventListener('change', syncIsMobile)
    coarsePointerMql?.removeEventListener('change', syncIsMobile)
    anyCoarsePointerMql?.removeEventListener('change', syncIsMobile)
    window.removeEventListener('resize', syncIsMobile)
    window.visualViewport?.removeEventListener('resize', syncIsMobile)
  })

  return { isMobile }
}
