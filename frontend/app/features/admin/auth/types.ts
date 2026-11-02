export type UserRole = 'admin' | 'manager'

export interface User {
  id: number
  login: string
  name: string
  role: UserRole
}

export interface TokenResponse {
  access_token: string
  user: User
}

export interface LoginPayload {
  login: string
  password: string
}
