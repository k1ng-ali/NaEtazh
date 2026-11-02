import type { LoginPayload, TokenResponse } from './types'

// Refresh-токен лежит в httpOnly cookie, поэтому запросы входа идут с credentials
export const useAuthApi = () => {
  const http = $fetch.create({ baseURL: useRuntimeConfig().public.apiUrl, credentials: 'include' })

  return {
    login: (payload: LoginPayload) => http<TokenResponse>('/auth/login', { method: 'POST', body: payload }),
    refresh: () => http<TokenResponse>('/auth/refresh', { method: 'POST' }),
    logout: () => http('/auth/logout', { method: 'POST' }),
  }
}
