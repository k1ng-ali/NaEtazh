import type { UserRole } from '../auth/types'

export interface StaffUser {
  id: number
  login: string
  name: string
  role: UserRole
  is_active: boolean
  last_login_at: string | null
  created_at: string
}

export interface StaffUserCreate {
  login: string
  name: string
  role: UserRole
  password: string
}

export interface StaffUserUpdate {
  name?: string
  role?: UserRole
  is_active?: boolean
}
