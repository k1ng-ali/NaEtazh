import { HOME_BY_ROLE } from '~/features/staff/auth/roles'
import { useAuthStore } from '~/features/staff/auth/store'

// После перезагрузки страницы токена в памяти нет, пробуем восстановить сессию по cookie
export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  const isLoginPage = to.path === '/login'

  if (!auth.isAuthenticated && !auth.isSessionChecked) await auth.refresh()

  if (!auth.isAuthenticated || !auth.user) {
    return isLoginPage ? undefined : navigateTo({ path: '/login', query: { next: to.fullPath } })
  }

  const home = HOME_BY_ROLE[auth.user.role]
  if (isLoginPage) return navigateTo(home)
  // Чужой кабинет не открываем, а отправляем в свой. Сервер всё равно проверит права
  if (to.meta.roles && !to.meta.roles.includes(auth.user.role)) return navigateTo(home)
})
