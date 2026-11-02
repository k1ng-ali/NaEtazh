import type { UserRole } from '~/features/staff/auth/types'

declare module '#app' {
  interface PageMeta {
    // Кто из сотрудников может открыть страницу, проверяет middleware staff
    roles?: UserRole[]
  }
}

export {}
