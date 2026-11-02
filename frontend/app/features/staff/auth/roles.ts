import type { UserRole } from './types'

// Куда попадает сотрудник после входа и при попытке открыть чужой кабинет
export const HOME_BY_ROLE: Record<UserRole, string> = {
  admin: '/admin',
  manager: '/manager/orders',
  courier: '/courier',
}

export const ROLE_LABEL: Record<UserRole, string> = {
  admin: 'Владелец',
  manager: 'Менеджер',
  courier: 'Курьер',
}

// Кабинет менеджера открыт и владельцу: он может работать с заказами сам
export const MANAGER_ROLES: UserRole[] = ['admin', 'manager']
export const ADMIN_ROLES: UserRole[] = ['admin']
export const COURIER_ROLES: UserRole[] = ['courier']
