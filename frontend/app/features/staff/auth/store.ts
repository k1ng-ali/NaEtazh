import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useAuthApi } from './api'
import type { LoginPayload, TokenResponse, User } from './types'

export const useAuthStore = defineStore('auth', () => {
  const api = useAuthApi()

  // ── State ──
  // Access-токен только в памяти: после перезагрузки страницы восстанавливается через refresh
  const accessToken = ref<string | null>(null)
  const user = ref<User | null>(null)
  // Сессию по cookie проверяем один раз за загрузку страницы, а не на каждом переходе
  const isSessionChecked = ref(false)
  let refreshing: Promise<boolean> | null = null

  // ── Getters ──
  const isAuthenticated = computed(() => accessToken.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // ── Actions ──
  function apply(response: TokenResponse) {
    accessToken.value = response.access_token
    user.value = response.user
  }

  function reset() {
    accessToken.value = null
    user.value = null
  }

  async function login(payload: LoginPayload) {
    apply(await api.login(payload))
  }

  // Параллельные запросы с истёкшим токеном ждут один общий refresh
  function refresh(): Promise<boolean> {
    refreshing ??= api
      .refresh()
      .then((response) => {
        apply(response)
        return true
      })
      .catch(() => {
        reset()
        return false
      })
      .finally(() => {
        isSessionChecked.value = true
        refreshing = null
      })
    return refreshing
  }

  async function logout() {
    try {
      await api.logout()
    } finally {
      reset()
    }
  }

  return { accessToken, user, isSessionChecked, isAuthenticated, isAdmin, login, refresh, logout, reset }
})
