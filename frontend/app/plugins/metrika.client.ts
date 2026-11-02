import { watch } from 'vue'
import { loadMetrika, trackPage } from '~/features/analytics/metrika'
import { useCookieStore } from '~/features/cookies/store'

// Метрика только на витрине и только после «Принять все» в cookie-баннере
const STAFF_PATHS = /^\/(admin|manager|courier|login)(\/|$)/

export default defineNuxtPlugin(() => {
  const id = Number(useRuntimeConfig().public.metrikaId)
  if (!id) return

  const router = useRouter()
  const cookies = useCookieStore()
  // Первый переход и согласие могут прийти одновременно: просмотр считаем один раз
  let lastTracked = ''

  function track(path: string, referer?: string) {
    if (!cookies.analyticsAllowed || STAFF_PATHS.test(path) || path === lastTracked) return
    loadMetrika(id)
    trackPage(path, referer)
    lastTracked = path
  }

  watch(
    () => cookies.analyticsAllowed,
    () => track(router.currentRoute.value.fullPath),
    { immediate: true },
  )

  router.afterEach((to, from) => track(to.fullPath, from.fullPath))
})
