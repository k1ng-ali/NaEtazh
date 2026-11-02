import { useStaffHttp } from '../shared/http'
import type { StaffUser, StaffUserCreate, StaffUserUpdate } from './types'

export const useUsersApi = () => {
  const http = useStaffHttp()

  return {
    listUsers: () => http<StaffUser[]>('/admin/users/'),
    createUser: (payload: StaffUserCreate) => http<StaffUser>('/admin/users/', { method: 'POST', body: payload }),
    updateUser: (id: number, payload: StaffUserUpdate) =>
      http<StaffUser>(`/admin/users/${id}`, { method: 'PATCH', body: payload }),
    setPassword: (id: number, password: string) =>
      http<void>(`/admin/users/${id}/password`, { method: 'PUT', body: { password } }),
  }
}
