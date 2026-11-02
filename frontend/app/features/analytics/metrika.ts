import { useLocationStore } from '~/features/location/store'

// Воронка: скан QR → товар в корзине → оформление → заказ.
// Те же имена нужно завести целями «JavaScript-событие» в интерфейсе Метрики
export const GOAL = {
  qrScan: 'qr_scan',
  addToCart: 'add_to_cart',
  checkoutStart: 'checkout_start',
  orderCreated: 'order_created',
} as const

export type Goal = (typeof GOAL)[keyof typeof GOAL]

type Ym = ((id: number, method: string, ...args: unknown[]) => void) & { a?: unknown[][]; l?: number }

declare global {
  interface Window {
    ym?: Ym
  }
}

let counterId: number | null = null

// Скрипт подключается один раз, только после согласия на аналитические cookie
export function loadMetrika(id: number) {
  if (counterId !== null) return
  counterId = id

  // Очередь до загрузки tag.js — так устроен официальный код счётчика
  const ym: Ym = (...args) => {
    ;(ym.a = ym.a ?? []).push(args)
  }
  ym.l = Date.now()
  window.ym = ym

  const script = document.createElement('script')
  script.async = true
  script.src = 'https://mc.yandex.ru/metrika/tag.js'
  document.head.appendChild(script)

  // defer: просмотры страниц отправляем сами при переходах внутри сайта
  ym(id, 'init', { defer: true, clickmap: true, trackLinks: true, accurateTrackBounce: true })
}

export function trackPage(url: string, referer?: string) {
  if (counterId === null) return
  window.ym?.(counterId, 'hit', url, { referer })
}

// Цель с кодом корпуса: в отчёте Метрики воронку можно разбить по корпусам
export function reachGoal(goal: Goal, params: Record<string, unknown> = {}) {
  if (counterId === null) return
  const building = useLocationStore().sourceCode
  window.ym?.(counterId, 'reachGoal', goal, { building: building ?? 'без QR', ...params })
}
