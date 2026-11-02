import { useAuthStore } from '../auth/store'

type RequestOptions = Omit<NonNullable<Parameters<typeof $fetch>[1]>, 'headers'>

// Запросы админки: подставляет токен и один раз обновляет его при 401
export const useAdminHttp = () => {
  const auth = useAuthStore()
  const http = $fetch.create({ baseURL: useRuntimeConfig().public.apiUrl })

  return async <T>(url: string, options: RequestOptions = {}): Promise<T> => {
    const send = () =>
      http<T>(url, {
        ...options,
        headers: auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {},
      }) as Promise<T>

    try {
      return await send()
    } catch (error) {
      if (getStatus(error) !== 401) throw error
      if (await auth.refresh()) return await send()
      await navigateTo('/admin/login')
      throw error
    }
  }
}

export const getStatus = (error: unknown): number | undefined =>
  (error as { response?: { status?: number } })?.response?.status
