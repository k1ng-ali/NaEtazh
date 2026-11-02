import { useStaffHttp } from '../shared/http'
import type { Dashboard } from './types'

export const useDashboardApi = () => {
  const http = useStaffHttp()

  return {
    getDashboard: (days: number) => http<Dashboard>('/admin/dashboard/', { query: { days } }),
  }
}
