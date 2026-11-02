import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { readJson, writeJson } from '~/shared/lib/storage'

const STORAGE_KEY = 'sb97-cookies'

// all — разрешена аналитика, necessary — только работа сайта
export type CookieChoice = 'all' | 'necessary'

// Выбор покупателя в cookie-баннере. Метрика подключается, только когда analyticsAllowed
export const useCookieStore = defineStore('cookies', () => {
  // ── State ──
  const choice = ref<CookieChoice | null>(null)
  const isHydrated = ref(false)

  // ── Getters ──
  const analyticsAllowed = computed(() => choice.value === 'all')
  const needsChoice = computed(() => isHydrated.value && choice.value === null)

  // ── Actions ──
  function choose(value: CookieChoice) {
    choice.value = value
    writeJson(STORAGE_KEY, value)
  }

  function hydrate() {
    const saved = readJson<CookieChoice | null>(STORAGE_KEY, null)
    choice.value = saved === 'all' || saved === 'necessary' ? saved : null
    isHydrated.value = true
  }

  return { choice, analyticsAllowed, needsChoice, choose, hydrate }
})
