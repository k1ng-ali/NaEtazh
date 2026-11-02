import { useAuthStore } from '~/features/admin/auth/store'

// После перезагрузки страницы токена в памяти нет, пробуем восстановить сессию по cookie
export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  const isLoginPage = to.path === '/admin/login'

  if (!auth.isAuthenticated && !auth.isSessionChecked) await auth.refresh()

  if (!auth.isAuthenticated && !isLoginPage) {
    return navigateTo({ path: '/admin/login', query: { next: to.fullPath } })
  }
  if (auth.isAuthenticated && isLoginPage) return navigateTo('/admin/orders')
})
